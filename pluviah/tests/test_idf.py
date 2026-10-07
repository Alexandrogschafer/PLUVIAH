# tests/test_idf.py

import numpy as np
import pandas as pd
import pytest
from scipy.stats import pearson3, genextreme
from idf import calculate_annual_maxima, calculate_idf_curves, calcular_chuva_projeto

@pytest.fixture
def serie_chuva_exemplo():
    """
    Cria um DataFrame do Pandas de exemplo para ser usado nos testes.
    Isso é uma "fixture" do pytest.
    """
    datas = pd.to_datetime([
        '2020-01-10 10:00', '2020-01-10 11:00', '2020-01-10 12:00', # Ano 2020
        '2021-05-20 08:00', '2021-05-20 09:00', '2021-05-20 10:00'  # Ano 2021
    ])
    precipitacao = [10, 25, 5, 8, 15, 30] # mm
    df = pd.DataFrame({'precipitacao': precipitacao}, index=datas)
    return df

def test_maxima_anual_duracao_1h(serie_chuva_exemplo):
    """
    Testa o cálculo da máxima anual para duração de 1 hora (o próprio valor horário).
    """
    maximas = calculate_annual_maxima(serie_chuva_exemplo, duration=1)
    
    # Para 2020, o máximo horário foi 25. Para 2021, foi 30.
    assert maximas.loc[2020] == pytest.approx(25)
    assert maximas.loc[2021] == pytest.approx(30)
    assert len(maximas) == 2

def test_maxima_anual_duracao_2h(serie_chuva_exemplo):
    """
    Testa o cálculo da máxima anual para duração de 2 horas (soma móvel).
    """
    maximas = calculate_annual_maxima(serie_chuva_exemplo, duration=2)
    
    # Somas móveis para 2020: [10, 35, 30]. Máximo é 35.
    # Somas móveis para 2021: [8, 23, 45]. Máximo é 45.
    assert maximas.loc[2020] == pytest.approx(35)
    assert maximas.loc[2021] == pytest.approx(45)


def _serie_a_partir_de_log(valores_log, ano_inicial=1980):
    """Monta uma Serie de maximas anuais (mm) a partir de valores em escala log10."""
    valores = 10 ** np.asarray(valores_log)
    return pd.Series(valores, index=range(ano_inicial, ano_inicial + len(valores)))


def test_calculate_idf_curves_inclui_teste_de_aderencia_lp3():
    """
    calculate_idf_curves deve computar um teste de aderencia (K-S e Anderson-Darling)
    para o ajuste Log-Pearson III, nao apenas para o Gumbel.
    """
    rng = np.random.default_rng(7)
    log_amostra = pearson3.rvs(0.4, loc=1.0, scale=0.15, size=40, random_state=rng)
    serie = _serie_a_partir_de_log(log_amostra)

    _, _, params_lp3, _, _, _, _, _ = calculate_idf_curves(serie, duration=1, trs_np=np.array([2, 5, 10, 25, 50, 100]))

    for chave in ("ks_p", "ad_stat", "ad_p"):
        assert chave in params_lp3

    assert 0.0 <= params_lp3["ks_p"] <= 1.0
    assert 0.0 <= params_lp3["ad_p"] <= 1.0
    assert params_lp3["ad_stat"] >= 0.0


def test_lp3_aderencia_boa_vs_ma():
    """
    Uma amostra gerada por uma Pearson III (em escala log10) deve produzir um
    p-valor alto (boa aderencia). Uma amostra claramente bimodal — que nenhuma
    Pearson III unimodal consegue descrever, mesmo casando media/desvio/assimetria —
    deve produzir um p-valor baixo (ma aderencia), tanto no K-S quanto no Anderson-Darling.
    """
    rng = np.random.default_rng(7)

    log_boa = pearson3.rvs(0.4, loc=1.0, scale=0.15, size=40, random_state=rng)
    serie_boa = _serie_a_partir_de_log(log_boa)

    cluster1 = 0.5 + 0.02 * rng.standard_normal(20)
    cluster2 = 2.5 + 0.02 * rng.standard_normal(20)
    log_ma = np.concatenate([cluster1, cluster2])
    serie_ma = _serie_a_partir_de_log(log_ma)

    trs = np.array([2, 5, 10, 25, 50, 100])
    _, _, params_boa, _, _, _, _, _ = calculate_idf_curves(serie_boa, duration=1, trs_np=trs)
    _, _, params_ma, _, _, _, _, _ = calculate_idf_curves(serie_ma, duration=1, trs_np=trs)

    assert params_boa["ks_p"] > 0.05
    assert params_boa["ad_p"] > 0.05

    assert params_ma["ks_p"] < 0.05
    assert params_ma["ad_p"] < 0.05


# --- Testes para calculate_idf_curves ---

TRS = np.array([2, 5, 10, 25, 50, 100])

@pytest.fixture
def maximas_anuais_exemplo():
    """Serie de 20 maximas anuais (mm) usada como caso de referencia."""
    valores = [42.0, 55.3, 61.8, 38.5, 70.2, 49.9, 83.4, 57.1, 46.7, 66.0,
               52.4, 91.5, 44.8, 59.6, 73.3, 50.5, 64.2, 47.9, 78.8, 56.4]
    return pd.Series(valores, index=range(2000, 2020))

def test_calculate_idf_curves_serie_curta():
    """Com menos de 5 anos de dados nao ha ajuste: todos os resultados sao None, menos a serie."""
    serie = pd.Series([30.0, 42.0, 51.0, 38.0], index=range(2000, 2004))
    df_idf, pg, pl, serie_ret, tg, tl, pgev, tgev = calculate_idf_curves(serie, duration=1, trs_np=TRS)
    assert df_idf is None and pg is None and pl is None and tg is None and tl is None
    assert pgev is None and tgev is None
    assert serie_ret is serie

def test_calculate_idf_curves_estrutura_da_tabela(maximas_anuais_exemplo):
    """A tabela IDF tem uma linha por TR e as colunas nomeadas pela duracao."""
    df_idf, _, _, _, _, _, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=2, trs_np=TRS)
    assert list(df_idf.columns) == [
        "TR (anos)", "Gumbel_2h (mm)", "LP3_2h (mm)", "GEV_2h (mm)",
        "Intensidade_Gumbel_2h (mm/h)", "Intensidade_LP3_2h (mm/h)", "Intensidade_GEV_2h (mm/h)",
    ]
    assert list(df_idf["TR (anos)"]) == list(TRS)

def test_calculate_idf_curves_intensidade_e_altura_sobre_duracao(maximas_anuais_exemplo):
    """Intensidade (mm/h) = altura precipitada (mm) / duracao (h)."""
    df_idf, _, _, _, _, _, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=4, trs_np=TRS)
    assert df_idf["Intensidade_Gumbel_4h (mm/h)"].values == pytest.approx(df_idf["Gumbel_4h (mm)"].values / 4)
    assert df_idf["Intensidade_LP3_4h (mm/h)"].values == pytest.approx(df_idf["LP3_4h (mm)"].values / 4)

def test_calculate_idf_curves_quantis_crescem_com_tr(maximas_anuais_exemplo):
    """A precipitacao estimada deve crescer com o periodo de retorno, nas duas distribuicoes."""
    df_idf, _, _, _, _, _, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    assert np.all(np.diff(df_idf["Gumbel_1h (mm)"].values) > 0)
    assert np.all(np.diff(df_idf["LP3_1h (mm)"].values) > 0)

def test_calculate_idf_curves_quantil_gumbel_formula_fechada(maximas_anuais_exemplo):
    """
    O quantil de Gumbel tem forma fechada: x_T = mu - beta * ln(-ln(1 - 1/T)).
    A tabela deve ser coerente com os parametros (mu, beta) retornados.
    """
    df_idf, params_gumbel, _, _, tupla_gumbel, _, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    mu, beta = tupla_gumbel
    assert (params_gumbel["mu"], params_gumbel["beta"]) == (mu, beta)
    esperado = mu - beta * np.log(-np.log(1 - 1 / TRS))
    assert df_idf["Gumbel_1h (mm)"].values == pytest.approx(esperado)

def test_calculate_idf_curves_parametros_lp3_sao_momentos_do_log10(maximas_anuais_exemplo):
    """Os parametros da LP3 sao a media, o desvio padrao amostral e a assimetria do log10 da serie."""
    _, _, params_lp3, _, _, tupla_lp3, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    logs = np.log10(maximas_anuais_exemplo.values)
    n = len(logs)
    media = logs.sum() / n
    desvio = np.sqrt(((logs - media) ** 2).sum() / (n - 1))
    # Assimetria amostral corrigida: n / ((n-1)(n-2)) * soma(((x - media) / s)^3)
    assimetria = n / ((n - 1) * (n - 2)) * (((logs - media) / desvio) ** 3).sum()
    assert params_lp3["mean_log"] == pytest.approx(media)
    assert params_lp3["std_log"] == pytest.approx(desvio)
    assert params_lp3["skew"] == pytest.approx(assimetria)
    assert tupla_lp3 == (params_lp3["mean_log"], params_lp3["std_log"], params_lp3["skew"])

def test_calculate_idf_curves_aderencia_gumbel(maximas_anuais_exemplo):
    """O ajuste Gumbel traz o p-valor do K-S e a estatistica/p-valor do Anderson-Darling."""
    _, params_gumbel, _, _, _, _, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    assert 0.0 <= params_gumbel["ks_p"] <= 1.0
    assert params_gumbel["ad_stat"] >= 0.0
    assert 0.0 <= params_gumbel["ad_p"] <= 1.0


# --- Testes para calcular_chuva_projeto ---

def test_chuva_projeto_gumbel_valor_conhecido():
    """
    mu=50, beta=10, TR=10 anos:
    x = 50 - 10 * ln(-ln(0.9)) = 50 + 10 * 2.25037 = 72.5037 mm.
    """
    chuva = calcular_chuva_projeto(10, "Gumbel", (50.0, 10.0), None)
    assert chuva == pytest.approx(72.5037, abs=1e-4)

def test_chuva_projeto_lp3_assimetria_nula_valor_conhecido():
    """
    Com assimetria zero a Pearson III se reduz a Normal, e o fator de frequencia e o z da Normal.
    media_log=1.5, desvio_log=0.2, TR=100 anos (z = 2.32635):
    x = 10^(1.5 + 2.32635 * 0.2) = 10^1.96527 = 92.31 mm.
    """
    chuva = calcular_chuva_projeto(100, "Log-Pearson III", None, (1.5, 0.2, 0.0))
    assert chuva == pytest.approx(92.31, abs=0.01)

def test_chuva_projeto_tr_2_anos_gumbel_e_a_mediana():
    """TR=2 anos corresponde a mediana: x = mu - beta * ln(ln 2)."""
    chuva = calcular_chuva_projeto(2, "Gumbel", (50.0, 10.0), None)
    assert chuva == pytest.approx(50.0 - 10.0 * np.log(np.log(2.0)))

def test_chuva_projeto_cresce_com_tr():
    """Maior periodo de retorno, maior chuva de projeto, nos dois metodos."""
    gumbel, lp3 = (50.0, 10.0), (1.5, 0.2, 0.3)
    for metodo in ("Gumbel", "Log-Pearson III"):
        valores = [calcular_chuva_projeto(tr, metodo, gumbel, lp3) for tr in (2, 10, 50, 100)]
        assert valores == sorted(valores) and len(set(valores)) == 4

def test_chuva_projeto_coerente_com_a_tabela_idf(maximas_anuais_exemplo):
    """A chuva de projeto calculada com os parametros ajustados deve coincidir com a tabela IDF."""
    df_idf, _, _, _, tupla_gumbel, tupla_lp3, _, _ = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    linha_tr25 = df_idf[df_idf["TR (anos)"] == 25].iloc[0]
    assert calcular_chuva_projeto(25, "Gumbel", tupla_gumbel, tupla_lp3) == pytest.approx(linha_tr25["Gumbel_1h (mm)"])
    assert calcular_chuva_projeto(25, "Log-Pearson III", tupla_gumbel, tupla_lp3) == pytest.approx(linha_tr25["LP3_1h (mm)"])

def test_chuva_projeto_parametros_ausentes():
    """Sem os parametros do metodo escolhido a funcao deve levantar ValueError."""
    with pytest.raises(ValueError):
        calcular_chuva_projeto(10, "Gumbel", None, (1.5, 0.2, 0.0))
    with pytest.raises(ValueError):
        calcular_chuva_projeto(10, "Log-Pearson III", (50.0, 10.0), None)

def test_chuva_projeto_metodo_invalido():
    """Um metodo desconhecido deve levantar ValueError."""
    with pytest.raises(ValueError):
        calcular_chuva_projeto(10, "Weibull", (50.0, 10.0), (1.5, 0.2, 0.0))


# --- Testes para a distribuicao GEV ---

def test_gev_parametros_e_aderencia(maximas_anuais_exemplo):
    """O ajuste GEV traz forma (xi), posicao, escala e os testes de aderencia K-S e Anderson-Darling."""
    resultado = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    params_gev, tupla_gev = resultado[6], resultado[7]
    for chave in ("xi", "loc", "scale", "ks_p", "ad_stat", "ad_p"):
        assert chave in params_gev
    assert params_gev["scale"] > 0
    assert 0.0 <= params_gev["ks_p"] <= 1.0
    assert 0.0 <= params_gev["ad_p"] <= 1.0
    assert tupla_gev == (params_gev["xi"], params_gev["loc"], params_gev["scale"])

def test_gev_quantil_formula_fechada(maximas_anuais_exemplo):
    """
    Quantil da GEV na convencao xi: x_T = mu + (sigma / xi) * ((-ln(1 - 1/T))^(-xi) - 1).
    A tabela deve ser coerente com os parametros retornados (isso tambem fixa o sinal de xi).
    """
    resultado = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    df_idf, (xi, mu, sigma) = resultado[0], resultado[7]
    esperado = mu + (sigma / xi) * ((-np.log(1 - 1 / TRS)) ** (-xi) - 1)
    assert df_idf["GEV_1h (mm)"].values == pytest.approx(esperado)
    assert np.all(np.diff(df_idf["GEV_1h (mm)"].values) > 0)
    assert df_idf["Intensidade_GEV_1h (mm/h)"].values == pytest.approx(df_idf["GEV_1h (mm)"].values)

def test_gev_recupera_parametros_de_amostra_sintetica():
    """Amostra grande gerada por uma GEV conhecida (xi=0.1, mu=60, sigma=15): o ajuste recupera os parametros."""
    amostra = genextreme.rvs(-0.1, loc=60.0, scale=15.0, size=500, random_state=np.random.default_rng(11))
    serie = pd.Series(amostra, index=range(500))
    resultado = calculate_idf_curves(serie, duration=1, trs_np=TRS)
    xi, mu, sigma = resultado[7]
    assert xi == pytest.approx(0.1, abs=0.05)
    assert mu == pytest.approx(60.0, rel=0.03)
    assert sigma == pytest.approx(15.0, rel=0.06)
    assert resultado[6]["ks_p"] > 0.05

def test_chuva_projeto_gev_valor_conhecido():
    """
    xi=0.1, mu=50, sigma=10, TR=100 anos:
    x = 50 + (10 / 0.1) * ((-ln(0.99))^(-0.1) - 1) = 50 + 100 * (1.58412 - 1) = 108.41 mm.
    """
    chuva = calcular_chuva_projeto(100, "GEV", None, None, gev_params=(0.1, 50.0, 10.0))
    assert chuva == pytest.approx(108.41, abs=0.01)

def test_chuva_projeto_gev_forma_nula_equivale_a_gumbel():
    """Com xi = 0 a GEV se reduz a Gumbel de mesma posicao e escala."""
    gev = calcular_chuva_projeto(25, "GEV", None, None, gev_params=(0.0, 50.0, 10.0))
    gumbel = calcular_chuva_projeto(25, "Gumbel", (50.0, 10.0), None)
    assert gev == pytest.approx(gumbel)

def test_chuva_projeto_gev_coerente_com_a_tabela_idf(maximas_anuais_exemplo):
    """A chuva de projeto pela GEV deve coincidir com a coluna GEV da tabela IDF."""
    resultado = calculate_idf_curves(maximas_anuais_exemplo, duration=1, trs_np=TRS)
    df_idf, tupla_gev = resultado[0], resultado[7]
    linha_tr50 = df_idf[df_idf["TR (anos)"] == 50].iloc[0]
    assert calcular_chuva_projeto(50, "GEV", None, None, gev_params=tupla_gev) == pytest.approx(linha_tr50["GEV_1h (mm)"])

def test_chuva_projeto_gev_parametros_ausentes():
    """Sem os parametros da GEV a funcao deve levantar ValueError."""
    with pytest.raises(ValueError):
        calcular_chuva_projeto(10, "GEV", (50.0, 10.0), (1.5, 0.2, 0.0))
