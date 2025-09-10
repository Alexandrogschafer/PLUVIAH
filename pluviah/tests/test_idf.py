# tests/test_idf.py

import pandas as pd
import pytest
from idf import calculate_annual_maxima

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
