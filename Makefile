PYTHON := .venv-judge/bin/python

.PHONY: stats router clean-stats clean-router

STATS_OUTPUTS := \
  results/stats/per_stratum_f1_ci.csv \
  results/stats/pairwise_delta_ci.csv \
  results/stats/significance_matrix.csv \
  results/stats/judge_agreement.csv \
  results/stats/faithfulness_ci.csv \
  figures/fig1_per_stratum_f1.pdf \
  figures/fig2_faithfulness_heatmap.pdf

ROUTER_OUTPUTS := \
  data/router/features.csv \
  data/router/v2_oof_routes.csv \
  data/router/oracle_routes.csv \
  results/router/v2_cv_report.txt \
  results/router/v2_acceptance.txt \
  results/stats/adaptive_comparison.csv

stats: $(STATS_OUTPUTS)
router: $(ROUTER_OUTPUTS)

data/router/features.csv: scripts/router/v2_features.py results/main-v2-scored.csv
	$(PYTHON) scripts/router/v2_features.py

data/router/v2_oof_routes.csv results/router/v2_cv_report.txt: \
		scripts/router/v2_train.py data/router/features.csv
	$(PYTHON) scripts/router/v2_train.py

data/router/oracle_routes.csv: scripts/router/oracle.py results/main-v2-scored.csv
	$(PYTHON) scripts/router/oracle.py

results/stats/adaptive_comparison.csv results/router/v2_acceptance.txt: \
		scripts/router/evaluate_adaptive.py \
		data/router/v2_oof_routes.csv \
		data/router/oracle_routes.csv \
		results/main-v2-scored.csv
	$(PYTHON) scripts/router/evaluate_adaptive.py

results/stats/per_stratum_f1_ci.csv results/stats/pairwise_delta_ci.csv: \
		scripts/stats/bootstrap_ci.py results/main-v2-scored.csv
	$(PYTHON) scripts/stats/bootstrap_ci.py

results/stats/significance_matrix.csv: \
		scripts/stats/significance_tests.py results/stats/pairwise_delta_ci.csv
	$(PYTHON) scripts/stats/significance_tests.py

results/stats/judge_agreement.csv results/stats/faithfulness_ci.csv: \
		scripts/stats/faithfulness_ci.py results/main-v2-judged.csv
	$(PYTHON) scripts/stats/faithfulness_ci.py

figures/fig1_per_stratum_f1.pdf figures/fig2_faithfulness_heatmap.pdf: \
		scripts/stats/figures.py \
		results/stats/per_stratum_f1_ci.csv \
		results/stats/significance_matrix.csv \
		results/stats/faithfulness_ci.csv \
		results/stats/judge_agreement.csv
	$(PYTHON) scripts/stats/figures.py

clean-stats:
	rm -rf results/stats figures/fig1_per_stratum_f1.pdf figures/fig2_faithfulness_heatmap.pdf

clean-router:
	rm -rf data/router results/router results/stats/adaptive_comparison.csv

.PHONY: paper-tables paper

PAPER_TABLES := \
  paper/cikm/tables/table_main.tex \
  paper/cikm/tables/table_faithfulness.tex \
  paper/cikm/tables/table_agreement.tex

$(PAPER_TABLES): scripts/tex/make_tables.py \
		results/stats/per_stratum_f1_ci.csv \
		results/stats/significance_matrix.csv \
		results/stats/faithfulness_ci.csv \
		results/stats/judge_agreement.csv \
		results/stats/adaptive_comparison.csv \
		results/main-v2-scored.csv
	$(PYTHON) scripts/tex/make_tables.py

paper-tables: $(PAPER_TABLES)

paper: paper-tables
	cp -f figures/fig1_per_stratum_f1.pdf paper/cikm/figures/
	cp -f figures/fig2_faithfulness_heatmap.pdf paper/cikm/figures/
	$(MAKE) -C paper/cikm
