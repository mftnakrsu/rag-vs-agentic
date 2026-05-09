"""Reranker behind a uniform interface.

    rerank(query, candidates, *, top_n=5, text_field='full_text') -> list[dict]

Each returned chunk gets a `_rerank_score` field (descending, higher = better).

Azure: Cohere rerank-v4.0-fast on Foundry — POST {base}/providers/cohere/v2/rerank
       (proxy path; portal-shown URL is wrong per known UI bug). No api-version
       query parameter. 1000 TPM cap, so the wrapper truncates docs and paces.
Local BGE reranker is intentionally absent — weights not on disk.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List

import httpx


def _pick_device() -> str:
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class LocalBGEReranker:
    """bge-reranker-v2-m3 cross-encoder, loaded from local model dir."""

    MAX_TOKENS = 512

    def __init__(self, model_path: str | None = None):
        self._model_path = model_path or os.environ["LOCAL_RERANKER_MODEL_PATH"]
        self._model = None
        self._tokenizer = None
        self._device: str | None = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        d = Path(self._model_path)
        if not d.exists():
            raise FileNotFoundError(f"BGE reranker not found at {d}")

        self._tokenizer = AutoTokenizer.from_pretrained(str(d))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(d))
        self._device = _pick_device()
        self._model = self._model.to(self._device)
        self._model.eval()

    def rerank(
        self,
        query: str,
        candidates: List[dict],
        *,
        top_n: int = 5,
        text_field: str = "full_text",
    ) -> List[dict]:
        if not candidates:
            return []
        import torch

        self._load()
        pairs = [(query, c[text_field]) for c in candidates]
        inputs = self._tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=self.MAX_TOKENS,
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            scores = self._model(**inputs).logits.view(-1).float().cpu().numpy()

        scored: List[dict] = []
        for c, s in zip(candidates, scores):
            c2 = dict(c)
            c2["_rerank_score"] = float(s)
            scored.append(c2)
        scored.sort(key=lambda x: x["_rerank_score"], reverse=True)
        return scored[:top_n]


class AzureCohereReranker:
    """Azure-hosted Cohere rerank-v4.0-fast via Foundry serverless endpoint.

    The 1000 TPM cap forces four mitigations:
      1. Truncate each doc to AZURE_RERANKER_MAX_DOC_CHARS (default 200 ≈ 50 tok).
      2. Cap input candidate count via `top_n_input` (default 10).
      3. Sleep AZURE_RERANKER_MIN_INTERVAL_S between calls (default 15s).
      4. Pacing state lives on the CLASS, not the instance, so the timer
         persists across `get_reranker()` calls in `compare.py` (which
         creates a fresh reranker per row).
    """

    # Shared across all instances — `compare.py` creates a new instance per
    # ablation row, but the rate-limit budget is global to this process.
    _shared_last_call: float = 0.0

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        deployment: str | None = None,
        path: str | None = None,
        max_doc_chars: int | None = None,
        min_interval_s: float | None = None,
    ):
        self.base_url = (base_url or os.environ["AZURE_RERANKER_BASE_URL"]).rstrip("/")
        self.api_key = api_key or os.environ["AZURE_RERANKER_API_KEY"]
        self.deployment = deployment or os.environ["AZURE_RERANKER_DEPLOYMENT"]
        self.path = path or os.environ.get("AZURE_RERANKER_PATH", "/providers/cohere/v2/rerank")
        self.max_doc_chars = int(
            max_doc_chars if max_doc_chars is not None
            else os.environ.get("AZURE_RERANKER_MAX_DOC_CHARS", 200)
        )
        self.min_interval_s = float(
            min_interval_s if min_interval_s is not None
            else os.environ.get("AZURE_RERANKER_MIN_INTERVAL_S", 15.0)
        )

    def _wait_for_budget(self) -> None:
        cls = type(self)
        elapsed = time.time() - cls._shared_last_call
        if 0 < elapsed < self.min_interval_s:
            time.sleep(self.min_interval_s - elapsed)
        cls._shared_last_call = time.time()

    def rerank(
        self,
        query: str,
        candidates: List[dict],
        *,
        top_n: int = 5,
        top_n_input: int = 10,
        text_field: str = "full_text",
    ) -> List[dict]:
        if not candidates:
            return []
        # Hard-cap input to keep within 1000 TPM.
        cands = candidates[:top_n_input]
        docs = [c[text_field][: self.max_doc_chars] for c in cands]

        self._wait_for_budget()
        url = f"{self.base_url}{self.path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.deployment,
            "query": query[: self.max_doc_chars],
            "documents": docs,
            "top_n": min(top_n, len(cands)),
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", "30"))
                time.sleep(retry_after)
                self._last_call = time.time()
                resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Cohere v2 response: {"results": [{"index": int, "relevance_score": float}, ...]}
        out: List[dict] = []
        for r in data.get("results", []):
            idx = r["index"]
            c2 = dict(cands[idx])
            c2["_rerank_score"] = float(r.get("relevance_score", 0.0))
            out.append(c2)
        return out


def get_reranker(name: str):
    """Factory: 'local'|'bge' or 'azure'|'cohere' -> reranker instance."""
    n = name.lower()
    if n in ("local", "bge", "local_bge"):
        return LocalBGEReranker()
    if n in ("azure", "cohere", "azure_cohere"):
        return AzureCohereReranker()
    raise ValueError(f"Unknown reranker: {name!r}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    sample = [
        {"id": "ADS-014", "full_text": "The ADS shall detect a blocked pitot port within 3 s."},
        {"id": "FCC-022", "full_text": "The FCC shall use AOA from ADS for envelope protection."},
        {"id": "PWR-012", "full_text": "Independent power feeds for redundant LRUs."},
    ]
    q = "How does the ADS detect a blocked pitot tube?"
    for name in ("local", "azure"):
        try:
            rr = get_reranker(name)
            out = rr.rerank(q, sample, top_n=3)
            print(f"{name:6s}", [(c["id"], round(c["_rerank_score"], 3)) for c in out])
        except Exception as e:
            print(f"{name:6s} ERROR {type(e).__name__}: {e}")
