# tests/test_tc.py

import pytest
from tc import calcular_tc_kirpich, calcular_tc_giandotti

# Usamos pytest.approx para lidar com a imprecisão de números de ponto flutuante (floats)
# Testes para a fórmula de Kirpich
def test_kirpich_calculo_correto():
    """
    Verifica se a fórmula de Kirpich retorna um valor conhecido para entradas conhecidas.
    Valores de referência calculados manualmente ou em outra ferramenta.
    """
    L_m = 1000  # metros
    i_m_per_m = 0.01 # m/m
    # Valor esperado: 0.0195 * (1000^0.77) * (0.01^-0.385) ≈ 23.44 minutos
    resultado_esperado = 23.44
    
    tc_calculado = calcular_tc_kirpich(L_m, i_m_per_m)
    
    assert tc_calculado == pytest.approx(resultado_esperado, rel=1e-2) # Tolerância de 1%

def test_kirpich_comportamento_fisico():
    """
    Verifica se, mantendo o comprimento, um declive maior (i) resulta em um Tc menor.
    """
    L_m = 1000
    i_menor = 0.01
    i_maior = 0.05
    
    tc_declive_menor = calcular_tc_kirpich(L_m, i_menor)
    tc_declive_maior = calcular_tc_kirpich(L_m, i_maior)
    
    assert tc_declive_maior < tc_declive_menor

# Testes para a fórmula de Giandotti
def test_giandotti_calculo_correto():
    """
    Verifica se a fórmula de Giandotti retorna um valor conhecido.
    """
    A_km2 = 10
    L_km = 5
    deltaH_m = 100
    # Valor esperado: ( (4 * 10 + 1.5 * 5) / (0.8 * 100) ) * 60 ≈ 35.625 minutos
    resultado_esperado = 35.625

    tc_calculado = calcular_tc_giandotti(A_km2, L_km, deltaH_m)
    
    assert tc_calculado == pytest.approx(resultado_esperado, rel=1e-3)
