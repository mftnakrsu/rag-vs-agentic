# RAG vs Agentic — Devam Noktası

> **Geri döndüğünde:** Bu dosyayı oku, sonra aşağıdaki **Quick resume** komutunu çalıştır.
> Tarih: 2026-05-09

---

## ⚡ Quick resume

```bash
cd /Users/suleakarsu/Desktop/rag-vs-agentic

# 1. Streamlit hâlâ çalışıyor mu?
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501/
#   → 200 ise zaten ayakta, tarayıcıda aç: http://localhost:8501
#   → değilse aşağıdaki komutu çalıştır:

# 2. Yoksa yeniden başlat
.venv/bin/streamlit run ui_app.py
```

Sonra **bana** dönüp tek cümleyle ne istediğini söyle. Ör:
- *"bildiriyi yaz"* — TR paper drafting'e geçeriz (önce format seçimi gerek, aşağıda)
- *"UI'da X şu sorun var"* — bug fix
- *"graphRAG ekleyelim"* — Neo4j Aura ile 3. pipeline

---

## 🎯 Şu an neredeyiz

| | Durum |
|---|---|
| Repo bootstrap (13 modül) | ✅ |
| venv 3.11 + deps (chromadb 1.5.9, langgraph 1.1.10, langchain-core 1.3.3, openai 2.36.0, torch 2.11.0, transformers 5.8.0, streamlit 1.57.0) | ✅ |
| ChromaDB index: `docs-local-e5` (384d) + `docs-azure` (1536d), her biri 1102 chunk | ✅ |
| Vanilla sanity (ADS-014 sorgusu) | ✅ 10.2s / 890 tok |
| Agentic sanity (cross-module ADS↔FCC) | ✅ 18.7s / 5658 tok, verdict=sufficient iter=0 |
| Full ablation matrix: **59/60** OK, 1100s wall | ✅ — `results/results.{csv,jsonl}` |
| README "Results" — delta tablosu + per-query notlar | ✅ |
| Streamlit UI — `ui_app.py` (side-by-side + canlı tool-call timeline + caching) | ✅ |
| **TR bildiri yazımı** | ⏳ **format seçimi bekliyor** |

### Headline sayılar (results section detayı README'de)

| Pipeline | Embedder | Rerank | Avg ms | Avg tok | Avg cited |
|---|---|---|---:|---:|---:|
| vanilla | azure | — | **3,822** | 706 | 5.0 |
| vanilla | local | — | 7,658 | 836 | 5.0 |
| agentic | azure | — | 14,277 | 4,573 | 3.0 |
| agentic | local | — | 20,181 | 5,343 | 2.8 |
| vanilla | local | azure-cohere | 31,269 | 738 | 5.0 |
| vanilla | azure | azure-cohere | 32,257 | 703 | 5.0 |

**Takeaway:** agentic 4-5× daha yavaş, 6-7× daha çok token; ama cross-module sorularda kaliteli (Q2'de ADS-012↔FCC-022 link'ini bulup transport bus'a kadar inebiliyor). Rerank 1000 TPM'de pacing yüzünden değer üretmiyor.

---

## ❓ Açık karar: TR bildiri formatı (geri dönünce seç)

| Opsiyon | Süre | Kapsam |
|---|---|---|
| **(a) Konferans bildirisi** (LaTeX, IEEE/ACM) | ~6-8 sayfa | Hangi konferans? UBMK, INISTA, ASYU…? |
| **(b) Türk dergi makalesi** (`.docx`/md) | ~10-15 sayfa | Pamukkale, ODTÜ, Bilişim Dergisi vb. |
| **(c) Pre-print / blog yazısı** (md) | daha kısa, gevşek | arxiv-tr veya kişisel blog |

Seçimini söyle, ben paper'ın iskeletini kurarım.

---

## 🔧 Kritik teknik notlar (unutulmasın)

### Azure Foundry URL conventions (öğrenilmesi pahalıydı)
- **LLM** `gpt-5.4-meftun` → `https://aif-shared-swedencentral1.services.ai.azure.com/api/projects/proj-shared-swedencentral/openai/v1` — `?api-version=...` **REJECTED**
- **Embedding** `text-embedding-3-small-meftun` → `https://...services.ai.azure.com/openai/v1` (resource-level, project değil) — api-version REJECTED
- **Reranker** `Cohere-rerank-v4.0-fast-meftun` → `https://...services.ai.azure.com/providers/cohere/v2/rerank` — **Azure portal yanlış URL gösteriyor (known UI bug)**. api-version YOK.

### Reranker pacing fixleri
- 1000 TPM cap → `AZURE_RERANKER_MIN_INTERVAL_S=15` (4'tü, çok agresif), `MAX_DOC_CHARS=200`
- `_last_call` instance-level → class-level shared state'e taşındı (`compare.py` her satırda fresh instance yaratıyordu, pacing reset oluyordu)

### Local model durumu
- e5-small ✅ (`/Users/suleakarsu/Desktop/doors_graphRAG/models/multilingual-e5-small`)
- bge-reranker-v2-m3 ❌ — sadece tokenizer var, weights yok. `LOCAL_RERANKER_MODEL_PATH` `.env`'den silindi. `compare.py` her zaman `--no-local-rerank` ile çalıştır.

### Streamlit caching
- `cached_graph(embedder_name)`, `cached_embedder(name)`, `cached_collection(...)`, `cached_reranker()` — ilk sorgudan sonra her şey bellekte. İlk agentic sorgu ~7-10s, sonrakiler ~3-5s.

### Neo4j Aura (offered, deferred)
- Chris'ten gelen Aura instance'ı (`reference_neo4j_aura.md` memory'de cred'ler) — şu an entegre değil. GraphRAG istersen ayrı bir 3. pipeline olarak ekle, mevcut karşılaştırmayı kirletme.

---

## 📁 Dosya map

```
agentic_rag.py    LangGraph StateGraph (router/id_lookup/retriever/tools/collect_chunks/critic/synthesizer)
vanilla_rag.py    Tek-shot RAG pipeline
llm_compat.py     Azure GPT-5 variant-aware client (raw openai SDK; ChatOpenAI #34328 sebebiyle bypass)
embedders.py      LocalE5Small + AzureOpenAI embedder
reranker.py       Azure Cohere reranker (LocalBGE class kalıyor ama kullanılmıyor)
vector_store.py   ChromaDB helpers
build_index.py    Dual-collection indexer
compare.py        Ablation matrix (60 satır default; --no-local-rerank şart)
eval_queries.py   10 hand-curated query
ui_app.py         Streamlit UI ⭐ yeni
.streamlit/       Theme config (dark, blue accent)
results/          results.csv + results.jsonl (60 satır)
README.md         Project doc + Results section (delta tablosu + research takeaway)
.env              Azure cred'leri (gitignored — Cohere reranker URL fix'i + local rerank silindi)
HANDOFF.md        ⭐ bu dosya
```

---

## 🧠 Memory dosyaları

`~/.claude/projects/-Users-suleakarsu-Desktop-rag-vs-agentic/memory/`:
- `MEMORY.md` — index
- `user_profile.md` — user role & preferences (terse, technical, deep LangGraph/Azure GPT-5 knowledge)
- `project_rag_comparison.md` — proje genel bakış
- `reference_data_and_models.md` — data + model paths (bge weights yok flag'lendi)
- `feedback_execution_autonomy.md` — "no cost concerns, you decide"
- `feedback_research_first.md` — "web research before brute-force probing"
- `reference_neo4j_aura.md` — Neo4j Aura cred (deferred)
- `feedback_handoff_convention.md` — ⭐ yeni: session sonu HANDOFF.md yazma kuralı

---

## 🚦 Background processes (kapanma sonrası kaybolur)

- `streamlit run ui_app.py` job `bsgdirrry` → http://localhost:8501 (Mac restart edersen kaybolur, Quick resume ile geri getir)

---

## Git durumu

Tüm değişiklikler **uncommitted**. Commit edilmesi istenirse:
```bash
git add -A && git status   # önce gör
# user onayı sonrası:
# git commit ile mesaj yaz
```
Şu ana kadar user commit/push istemedi.
