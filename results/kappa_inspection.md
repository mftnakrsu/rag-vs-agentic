# Multi-judge κ inspection (GPT-5.4 × GPT-4.1)

**N = 300** judged rows. Gemini column 100% null → 2-judge effective.

## 1. Overall agreement

| metric | value |
|---|---:|
| n | 300 |
| GPT-5.4 faithful rate | 0.397 |
| GPT-4.1 faithful rate | 0.507 |
| Observed agreement P_o | 0.650 |
| Cohen P_e (chance) | 0.499 |
| **Cohen's κ** | **0.302** |
| **Gwet's AC1** | **0.306** |
| McNemar exact p (asymmetry) | 0.0017 |

_Kappa-paradox check: if AC1 ≫ κ then class skew is suppressing κ artificially._

## 2. Per-pipeline κ + AC1

| pipeline | n | GPT-5.4 fr | GPT-4.1 fr | P_o | Cohen κ | Gwet AC1 |
|---|---:|---:|---:|---:|---:|---:|
| adaptive | 60 | 0.350 | 0.400 | 0.717 | 0.397 | 0.467 |
| agentic | 60 | 0.383 | 0.500 | 0.650 | 0.300 | 0.309 |
| agentic-graph | 60 | 0.317 | 0.500 | 0.517 | 0.033 | 0.065 |
| graphrag | 60 | 0.617 | 0.683 | 0.600 | 0.125 | 0.266 |
| vanilla | 60 | 0.317 | 0.450 | 0.767 | 0.516 | 0.557 |

_Hypothesis: GraphRAG κ should be highest (both judges see the over-citation collapse)._

## 3. Per-stratum κ + AC1

| stratum | n | GPT-5.4 fr | GPT-4.1 fr | P_o | Cohen κ | Gwet AC1 |
|---|---:|---:|---:|---:|---:|---:|
| 1-hop | 95 | 0.537 | 0.779 | 0.653 | 0.275 | 0.368 |
| 2-hop | 111 | 0.441 | 0.550 | 0.604 | 0.216 | 0.207 |
| 3+-hop | 94 | 0.202 | 0.181 | 0.702 | 0.039 | 0.569 |

_Hypothesis: 3+-hop κ should be highest (both judges call answers unfaithful)._

## 4. Overall confusion matrix (GPT-5.4 rows × GPT-4.1 cols)

|  | GPT-4.1 ✓ | GPT-4.1 ✗ | row total |
|---|---:|---:|---:|
| **GPT-5.4 ✓** | 83 | 36 | 119 |
| **GPT-5.4 ✗** | 69 | 112 | 181 |
| col total | 152 | 148 | 300 |

GPT-5.4-only-faithful (b) = 36, GPT-4.1-only-faithful (c) = 69, net (b−c) = -33.
Sign of net > 0 means GPT-5.4 is more lenient than GPT-4.1; < 0 means the reverse. McNemar exact p = 0.0017.

## 5. Per-(stratum, pipeline) faithfulness rates

| stratum | pipeline | n | GPT-5.4 fr | GPT-4.1 fr | Δ (gpt5−gpt41) |
|---|---|---:|---:|---:|---:|
| 1-hop | adaptive | 18 | 0.444 | 0.778 | -0.333 |
| 1-hop | agentic | 19 | 0.474 | 0.737 | -0.263 |
| 1-hop | agentic-graph | 18 | 0.444 | 0.722 | -0.278 |
| 1-hop | graphrag | 23 | 0.739 | 0.783 | -0.043 |
| 1-hop | vanilla | 17 | 0.529 | 0.882 | -0.353 |
| 2-hop | adaptive | 23 | 0.435 | 0.304 | +0.130 |
| 2-hop | agentic | 26 | 0.423 | 0.500 | -0.077 |
| 2-hop | agentic-graph | 19 | 0.263 | 0.632 | -0.368 |
| 2-hop | graphrag | 22 | 0.636 | 0.818 | -0.182 |
| 2-hop | vanilla | 21 | 0.429 | 0.524 | -0.095 |
| 3+-hop | adaptive | 19 | 0.158 | 0.158 | +0.000 |
| 3+-hop | agentic | 15 | 0.200 | 0.200 | +0.000 |
| 3+-hop | agentic-graph | 23 | 0.261 | 0.217 | +0.043 |
| 3+-hop | graphrag | 15 | 0.400 | 0.333 | +0.067 |
| 3+-hop | vanilla | 22 | 0.045 | 0.045 | +0.000 |

## 6. Directional agreement (Spearman ρ)

**Overall ρ across 15 (stratum, pipeline) cells:** ρ = **0.922** (p = 0.0000)

- ρ near 1 → judges agree on the *ranking* of cells even if levels differ.
- ρ near 0 → judges disagree on direction; multi-judge methodology fails.

**Per-stratum ρ across 5 pipelines:**

| stratum | ρ | p | n cells |
|---|---:|---:|---:|
| 1-hop | 0.718 | 0.1718 | 5 |
| 2-hop | 0.100 | 0.8729 | 5 |
| 3+-hop | 1.000 | 0.0000 | 5 |

## 7. Per-pipeline monotonic stratum decline check

Does each judge see faithfulness drop monotonically as hops increase (1-hop ≥ 2-hop ≥ 3+-hop)?

| pipeline | GPT-5.4 (1h, 2h, 3+h) | GPT-4.1 (1h, 2h, 3+h) | both agree on decrease |
|---|---|---|---|
| adaptive | (0.44, 0.43, 0.16) | (0.78, 0.30, 0.16) | ✅ |
| agentic | (0.47, 0.42, 0.20) | (0.74, 0.50, 0.20) | ✅ |
| agentic-graph | (0.44, 0.26, 0.26) | (0.72, 0.63, 0.22) | ✅ |
| graphrag | (0.74, 0.64, 0.40) | (0.78, 0.82, 0.33) | ❌ |
| vanilla | (0.53, 0.43, 0.05) | (0.88, 0.52, 0.05) | ✅ |

## 8. GraphRAG faithfulness collapse (anchor verification)

GraphRAG 1-hop: GPT-5.4 = 74%, GPT-4.1 = 78% (n = 23)
GraphRAG 3+-hop: GPT-5.4 = 40%, GPT-4.1 = 33% (n = 15)
