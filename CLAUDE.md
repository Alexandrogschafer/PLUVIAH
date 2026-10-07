# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

codigo_projeto: PLUVIAH

## What this is

PLUVIAH is a Streamlit dashboard (in Portuguese) for hydrology/hydraulics analysis: rainfall series processing, IDF curve fitting (Gumbel / Log-Pearson III / GEV, with Monte Carlo goodness-of-fit tests), design storm estimation, time of concentration (Kirpich / Giandotti, with applicability-range alerts), design discharge (Rational Method), and circular conduit (commercial diameters) / open channel sizing (Manning), ending in a consolidated PDF report.

Current version is 1.1.0 (see `CHANGELOG.md`, which lists the changes that alter numerical results relative to v1.0.0). User-facing method documentation lives in `docs/manual.md`; when a change alters a formula, a default, or a displayed result, update both files.

## Commands

```bash
# Install
pip install -r requirements.txt
pip install -r requirements-dev.txt   # pytest, black, ruff, mypy

# Run the dashboard (must run from repo root so relative asset paths like "assets/logo.png" resolve)
streamlit run pluviah/dashboard.py

# Run all tests (from repo root)
pytest

# Run a single test file / test
pytest pluviah/tests/test_tc.py
pytest pluviah/tests/test_tc.py::test_kirpich_calculo_correto
```

The full suite takes about 35 s, almost all of it in `pluviah/tests/test_idf.py` (Monte Carlo goodness-of-fit). `pytest.ini` sets `pythonpath = .` so that `tests/test_imports.py` can `import pluviah` under bare `pytest` as well as `python -m pytest`.

There is no lint/format config file checked in; `black`, `ruff`, `mypy` are listed as dev dependencies but have no project config, so run them with their defaults if needed.

## Architecture

**Import style is flat, not package-relative.** Modules under `pluviah/` (`data_handler.py`, `idf.py`, `tc.py`, `racional.py`, `manning.py`, `relatorio.py`, `config.py`) import each other with bare names, e.g. `from tc import calcular_tc_kirpich`, `from config import G, RHO` — never `from pluviah.tc import ...`. `pluviah/` has no `__init__.py`. This works because:
- `streamlit run pluviah/dashboard.py` puts `pluviah/` on `sys.path`.
- `pluviah/tests/` has an `__init__.py` but `pluviah/` does not, so pytest's import-mode walks up to `pluviah/` as the "rootpath" and inserts it onto `sys.path`, making `tc`, `config`, etc. importable as top-level modules from the test files too.

When adding a new module in `pluviah/`, follow this same flat-import convention rather than introducing `pluviah.`-qualified imports — mixing the two will break under one of the two run modes.

**Layered structure**: `dashboard.py` is the only Streamlit-aware orchestration layer — it holds all UI (`st.*` calls), page routing (one `elif pagina_selecionada == "..."` block per sidebar tab), and cross-page state via `st.session_state`. All hydrology/hydraulics math is kept in plain, Streamlit-independent functions in `data_handler.py`, `idf.py`, `tc.py`, `racional.py`, and `manning.py`, which is what makes those functions unit-testable in isolation (see `pluviah/tests/`). The one exception is `relatorio.py`, which imports `streamlit` directly (for `@st.cache_data` on `gerar_pdf_bytes`) even though it's otherwise a pure PDF-building module (subclasses `fpdf.FPDF`).

**Cross-tab data flow via `st.session_state`**: results computed on one dashboard page feed into later pages entirely through `session_state` keys (no other shared state mechanism). The dependency chain is:
1. "Visão Geral" → loads `df` from an uploaded CSV via `data_handler.load_data`.
2. "Curvas IDF" → computes annual maxima + Gumbel/LP3/GEV fits → stores `idf_results` (the raw 8-tuple), `df_idf`, `gumbel_params_tuple`, `lp3_params_tuple`, `gev_params_tuple`, `params_gumbel`, `params_lp3`, `params_gev`, `duracao_idf_calculada`, `grafico_path` (a temp PNG of the IDF chart, used later by the PDF report).
3. "Chuva de Projeto" → reads the Gumbel/LP3/GEV param tuples, computes `chuva_proj_result` / `intensidade_proj_result`.
4. "Tempo de Concentração" → stores `tc_min` (not consumed by later pages, only by the PDF report).
5. "Vazão de Projeto" → reads `intensidade_proj_result`, computes `q_projeto` via the Rational Method (also stores `vazao_C`, `vazao_A`).
6. "Condutos Circulares" / "Canais Abertos" → read `q_projeto` as the default design discharge, compute conduit diameter or channel depth/width. The conduit page stores `conduto_d_teorico`, `conduto_dn_mm`, `conduto_d_rec`, `conduto_Q_calc`, `conduto_V`, `conduto_razao_yD`, `conduto_dentro_criterio`, and removes all of them when no diameter satisfies the design, so a stale result never reaches the PDF.
7. "Relatório PDF" → gates on `df_idf` and `grafico_path` being present, then assembles a `dados_para_relatorio` dict from whatever session_state keys were populated by earlier steps and passes it to `relatorio.gerar_pdf_bytes`.

Because of this, changing a `session_state` key name in one page's block requires updating every downstream page that reads it, plus the `dados_para_relatorio` dict in the "Relatório PDF" block.

**IDF fitting and goodness of fit** (`idf.py`): `calculate_idf_curves(series, duration, trs_np, n_mc=N_MC_ADERENCIA)` returns an 8-tuple `(df_idf, params_gumbel, params_lp3, series, gumbel_params_tuple, lp3_params_tuple, params_gev, gev_params_tuple)` (all `None` except `series` when there are fewer than 5 years). Gumbel and GEV are fit by maximum likelihood; LP3 by moments of the log10 series. The GEV shape is reported as ξ, while SciPy's `genextreme` uses `c = -ξ` — convert at the boundary. Each `params_*` dict carries `ks_stat`, `ks_p`, `ad_stat`, `ad_p` from `_teste_aderencia`, which calls `scipy.stats.goodness_of_fit` with `fit_params` (statistic measured against PLUVIAH's own fit) and **without** `known_params`, so parameters are re-estimated on every Monte Carlo sample; sample count and seed are `N_MC_ADERENCIA` / `SEMENTE_ADERENCIA` in `config.py`. This makes one call take ~40 s at the default 999 samples (the dashboard caches it), so tests must pass a small `n_mc` (see `N_MC_TESTE` in `test_idf.py`).

**Time of concentration** (`tc.py`): Giandotti is `Tc(h) = (4·√A + 1.5·L) / (0.8·√H)` with `H` = mean basin elevation minus outlet elevation (v1.0.0 had an incorrect formula without the square roots). `verificar_faixa_kirpich` / `verificar_faixa_giandotti` return a list of alert strings (empty when in range) against the `*_FAIXA_*` tuples in `config.py`; alerts are shown as warnings and never block the calculation.

**Circular conduit sizing** (`manning.py`): `dimensionar_conduto_circular(Q, n, S, diametros_mm, d_min_mm, criterio_yD)` returns `(dn_mm, q_capacidade)` for the smallest nominal diameter in `DIAMETROS_COMERCIAIS_CONCRETO_MM` that satisfies both full-section capacity ≥ Q and fill ratio y/D ≤ `criterio_yD` (`None` disables the second condition), or `(None, None)`. `diametro_teorico_circular` is the closed-form continuous minimum diameter, shown alongside the adopted DN. The velocity shown is for the design discharge at partial depth in the adopted DN, not the full-section velocity.

**Numerical solving pattern**: `manning.py`'s inverse hydraulic calculations (`y_normal`, `y_critico`, `b_para_Q`, and `razao_enchimento_conduto_circular` for the conduit fill ratio) are all root-finds of a closed-form forward function (`manning_Q`, `froude`) via the shared `bissecao` (bisection) helper — there's no `scipy.optimize` dependency for these paths. Any new "solve for X given Q" channel function should follow the same `def f(x): return forward_calc(...) - target; return bissecao(f, ...)` shape.

**Constants and lookups** (gravity, water density, Manning's n by material, commercial diameter series, Tc applicability ranges, Monte Carlo sample count and seed) live in `config.py` as flat module-level constants/dicts — not a class or settings object.

**Two test roots**: `tests/test_imports.py` at repo root only smoke-tests that the `pluviah` namespace package imports; the real unit tests (one file per math module, using `pytest.approx` against hand-computed reference values) live in `pluviah/tests/`.
