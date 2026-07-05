# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

PLUVIAH is a Streamlit dashboard (in Portuguese) for hydrology/hydraulics analysis: rainfall series processing, IDF curve fitting (Gumbel / Log-Pearson III), design storm estimation, time of concentration (Kirpich / Giandotti), design discharge (Rational Method), and circular conduit / open channel sizing (Manning), ending in a consolidated PDF report.

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

There is no lint/format config file checked in; `black`, `ruff`, `mypy` are listed as dev dependencies but have no project config, so run them with their defaults if needed.

## Architecture

**Import style is flat, not package-relative.** Modules under `pluviah/` (`data_handler.py`, `idf.py`, `tc.py`, `racional.py`, `manning.py`, `relatorio.py`, `config.py`) import each other with bare names, e.g. `from tc import calcular_tc_kirpich`, `from config import G, RHO` — never `from pluviah.tc import ...`. `pluviah/` has no `__init__.py`. This works because:
- `streamlit run pluviah/dashboard.py` puts `pluviah/` on `sys.path`.
- `pluviah/tests/` has an `__init__.py` but `pluviah/` does not, so pytest's import-mode walks up to `pluviah/` as the "rootpath" and inserts it onto `sys.path`, making `tc`, `config`, etc. importable as top-level modules from the test files too.

When adding a new module in `pluviah/`, follow this same flat-import convention rather than introducing `pluviah.`-qualified imports — mixing the two will break under one of the two run modes.

**Layered structure**: `dashboard.py` is the only Streamlit-aware orchestration layer — it holds all UI (`st.*` calls), page routing (one `elif pagina_selecionada == "..."` block per sidebar tab), and cross-page state via `st.session_state`. All hydrology/hydraulics math is kept in plain, Streamlit-independent functions in `data_handler.py`, `idf.py`, `tc.py`, `racional.py`, and `manning.py`, which is what makes those functions unit-testable in isolation (see `pluviah/tests/`). The one exception is `relatorio.py`, which imports `streamlit` directly (for `@st.cache_data` on `gerar_pdf_bytes`) even though it's otherwise a pure PDF-building module (subclasses `fpdf.FPDF`).

**Cross-tab data flow via `st.session_state`**: results computed on one dashboard page feed into later pages entirely through `session_state` keys (no other shared state mechanism). The dependency chain is:
1. "Visão Geral" → loads `df` from an uploaded CSV via `data_handler.load_data`.
2. "Curvas IDF" → computes annual maxima + Gumbel/LP3 fits → stores `df_idf`, `gumbel_params_tuple`, `lp3_params_tuple`, `duracao_idf_calculada`, `grafico_path` (a temp PNG of the IDF chart, used later by the PDF report).
3. "Chuva de Projeto" → reads the Gumbel/LP3 params, computes `chuva_proj_result` / `intensidade_proj_result`.
4. "Vazão de Projeto" → reads `intensidade_proj_result`, computes `q_projeto` via the Rational Method.
5. "Condutos Circulares" / "Canais Abertos" → read `q_projeto` as the default design discharge, compute conduit diameter or channel depth/width.
6. "Relatório PDF" → gates on `df_idf` and `grafico_path` being present, then assembles a `dados_para_relatorio` dict from whatever session_state keys were populated by earlier steps and passes it to `relatorio.gerar_pdf_bytes`.

Because of this, changing a `session_state` key name in one page's block requires updating every downstream page that reads it, plus the `dados_para_relatorio` dict in the "Relatório PDF" block.

**Numerical solving pattern**: `manning.py`'s inverse hydraulic calculations (`y_normal`, `y_critico`, `b_para_Q`) are all root-finds of a closed-form forward function (`manning_Q`, `froude`) via the shared `bissecao` (bisection) helper — there's no `scipy.optimize` dependency for these paths. Any new "solve for X given Q" channel function should follow the same `def f(x): return forward_calc(...) - target; return bissecao(f, ...)` shape.

**Constants and material lookups** (gravity, water density, Manning's n by material) live in `config.py` as flat module-level constants/dicts — not a class or settings object.

**Two test roots**: `tests/test_imports.py` at repo root only smoke-tests that the `pluviah` namespace package imports; the real unit tests (one file per math module, using `pytest.approx` against hand-computed reference values) live in `pluviah/tests/`.
