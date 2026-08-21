"""Two embedders behind a uniform interface.

    embed_query(str) -> list[float]
    embed_documents(list[str]) -> list[list[float]]

Embedder #1: LocalE5SmallEmbedder
    intfloat/multilingual-e5-small (loaded from disk)
    - 384-dim
    - mandatory `query: ` / `passage: ` prefixes
    - max 512 tokens (truncate)
    - mean-pool over attention mask + L2 normalize

Embedder #2: AzureOpenAIEmbedder
    Azure OpenAI text-embedding-3-* deployment (Foundry projects URL).
    - native 1536 dim for 3-small; can MRL-truncate via `dimensions` param.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from openai import OpenAI


def _pick_device() -> str:
    import torch
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class LocalE5SmallEmbedder:
    DIM = 384
    MAX_TOKENS = 512

    def __init__(self, model_path: str | None = None):
        self._model_path = model_path or os.environ["LOCAL_EMBEDDING_MODEL_PATH"]
        self._model = None
        self._tokenizer = None
        self._device: str | None = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoModel, AutoTokenizer

        d = Path(self._model_path)
        if not d.exists():
            raise FileNotFoundError(f"e5-small not found at {d}")

        self._tokenizer = AutoTokenizer.from_pretrained(str(d))
        self._model = AutoModel.from_pretrained(str(d))
        self._device = _pick_device()
        self._model = self._model.to(self._device)
        self._model.eval()

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        import torch
        import torch.nn.functional as F

        self._load()
        inputs = self._tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.MAX_TOKENS,
            return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            out = self._model(**inputs).last_hidden_state  # (B, T, H)
            mask = inputs["attention_mask"][..., None].bool()
            out = out.masked_fill(~mask, 0.0)
            pooled = out.sum(1) / inputs["attention_mask"].sum(1)[..., None]
            pooled = F.normalize(pooled, p=2, dim=1)

        return pooled.detach().cpu().float().numpy().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._embed([f"query: {text}"])[0]

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        prefixed = [f"passage: {t}" for t in texts]
        out: List[List[float]] = []
        for i in range(0, len(prefixed), batch_size):
            out.extend(self._embed(prefixed[i:i + batch_size]))
        return out


class AzureOpenAIEmbedder:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        deployment: str | None = None,
        api_version: str | None = None,
        dimension: int | None = None,
    ):
        self.base_url = base_url or os.environ["AZURE_OPENAI_EMBEDDING_BASE_URL"]
        self.api_key = api_key or os.environ["AZURE_OPENAI_EMBEDDING_API_KEY"]
        self.deployment = deployment or os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]
        self.api_version = api_version or os.environ.get(
            "AZURE_OPENAI_EMBEDDING_API_VERSION", "2025-04-01-preview"
        )
        self.dimension = int(
            dimension if dimension is not None
            else os.environ.get("AZURE_OPENAI_EMBEDDING_DIMENSION", 1536)
        )
        # Azure Foundry v1 endpoints (URL contains /openai/v1) use OpenAI-style
        # path versioning and reject ?api-version=...; legacy Azure OpenAI URLs
        # (.../openai/deployments/...) still need it as a query param.
        client_kwargs: dict = {"base_url": self.base_url, "api_key": self.api_key}
        if "/openai/v1" not in self.base_url:
            client_kwargs["default_query"] = {"api-version": self.api_version}
        self._client = OpenAI(**client_kwargs)

    @property
    def DIM(self) -> int:  # noqa: N802 — match LocalE5SmallEmbedder.DIM API
        return self.dimension

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        kwargs: dict = {"input": texts, "model": self.deployment}
        # text-embedding-3-* supports MRL truncation via `dimensions`. 3-small native is 1536;
        # only pass when actually truncating, otherwise omit (harmless either way).
        if 0 < self.dimension < 1536:
            kwargs["dimensions"] = self.dimension
        resp = self._client.embeddings.create(**kwargs)
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_batch([text])[0]

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        out: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            out.extend(self._embed_batch(texts[i:i + batch_size]))
        return out


class BGEM3Embedder(LocalE5SmallEmbedder):
    """BAAI/bge-m3 dense embeddings (1024d), the third embedder axis.

    Independent of both existing axes -- e5-small is Microsoft, 3-small is
    OpenAI -- so a reviewer cannot read it as a variant of what is already
    there. Weights come from the HF hub by name, not from a local path, so
    unlike the e5 setup it needs nothing staged on disk.

    bge-m3 takes the raw query with no "query: " prefix (that is an e5
    convention) and uses the CLS vector rather than mean pooling.
    """

    DIM = 1024
    MAX_TOKENS = 8192
    MODEL_ID = "BAAI/bge-m3"

    def __init__(self, model_path: str | None = None):
        super().__init__(model_path=model_path or self.MODEL_ID)

    def _load(self) -> None:
        if self._model is not None:
            return
        from transformers import AutoModel, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(self._model_path)
        self._model = AutoModel.from_pretrained(self._model_path)
        self._device = _pick_device()
        self._model = self._model.to(self._device)
        self._model.eval()

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """CLS pooling, as bge-m3's dense head is trained on the CLS vector.

        The inherited e5 implementation mean-pools, which would silently
        produce a different (and worse) embedding space here.
        """
        if not texts:
            return []
        import torch
        import torch.nn.functional as F

        self._load()
        inputs = self._tokenizer(
            texts, padding=True, truncation=True,
            max_length=self.MAX_TOKENS, return_tensors="pt",
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self._model(**inputs).last_hidden_state
            pooled = F.normalize(out[:, 0], p=2, dim=1)
        return pooled.detach().cpu().float().numpy().tolist()

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

    def embed_documents(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        out: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            out.extend(self._embed(texts[i:i + batch_size]))
        return out


def get_embedder(name: str):
    """Factory: 'local' | 'azure' | 'bge' -> embedder instance."""
    if name in ("local", "local_e5", "e5"):
        return LocalE5SmallEmbedder()
    if name in ("azure", "azure_openai"):
        return AzureOpenAIEmbedder()
    if name in ("bge", "bge-m3", "bgem3"):
        return BGEM3Embedder()
    raise ValueError(f"Unknown embedder: {name!r} (use 'local', 'azure' or 'bge')")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    for name in ("local", "azure"):
        emb = get_embedder(name)
        v = emb.embed_query("What does ADS-014 specify about pitot blockage?")
        print(f"{name:6s} dim={len(v)} sample[:3]={v[:3]}")
