# tests/test_idf.py

import numpy as np
import pandas as pd
import pytest
from scipy.stats import pearson3
from idf import calculate_annual_maxima, calculate_idf_curves

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

    _, _, params_lp3, _, _, _ = calculate_idf_curves(serie, duration=1, trs_np=np.array([2, 5, 10, 25, 50, 100]))

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
    _, _, params_boa, _, _, _ = calculate_idf_curves(serie_boa, duration=1, trs_np=trs)
    _, _, params_ma, _, _, _ = calculate_idf_curves(serie_ma, duration=1, trs_np=trs)

    assert params_boa["ks_p"] > 0.05
    assert params_boa["ad_p"] > 0.05

    assert params_ma["ks_p"] < 0.05
    assert params_ma["ad_p"] < 0.05
