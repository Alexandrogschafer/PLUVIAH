# tests/test_tc.py

import pytest
from tc import (
    calcular_tc_kirpich, calcular_tc_giandotti, verificar_faixa_kirpich, verificar_faixa_giandotti
)

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
    H_m = 100  # altitude média da bacia menos a cota do exutório
    # Valor esperado: (4 * sqrt(10) + 1.5 * 5) / (0.8 * sqrt(100)) * 60
    #               = (12.649 + 7.5) / 8 * 60 ≈ 151.12 minutos
    resultado_esperado = 151.12

    tc_calculado = calcular_tc_giandotti(A_km2, L_km, H_m)

    assert tc_calculado == pytest.approx(resultado_esperado, rel=1e-3)

def test_giandotti_comportamento_fisico():
    """
    Bacia maior ou talvegue mais longo aumentam o Tc; maior altura média o reduz.
    """
    tc_base = calcular_tc_giandotti(10, 5, 100)

    assert calcular_tc_giandotti(40, 5, 100) > tc_base
    assert calcular_tc_giandotti(10, 10, 100) > tc_base
    assert calcular_tc_giandotti(10, 5, 400) < tc_base

def test_giandotti_entrada_invalida():
    """
    Área, comprimento ou altura não positivos retornam 0.
    """
    assert calcular_tc_giandotti(10, 5, 0) == 0.0
    assert calcular_tc_giandotti(10, 5, -20) == 0.0
    assert calcular_tc_giandotti(0, 5, 100) == 0.0

# Testes para os alertas de faixa de aplicabilidade
def test_faixa_kirpich_dentro():
    """
    Bacia de 0,10 km², talvegue de 500 m e declividade de 0,05 m/m: dentro da faixa, sem alertas.
    """
    assert verificar_faixa_kirpich(A_km2=0.10, L_m=500, i_m_per_m=0.05) == []

def test_faixa_kirpich_fora():
    """
    Cada grandeza fora da faixa gera o seu alerta; o cálculo do Tc não é bloqueado.
    """
    # Área de 2 km² (máximo 0,45), comprimento de 3 km (máximo 1,19) e declividade de 0,005 (mínimo 0,02)
    alertas = verificar_faixa_kirpich(A_km2=2.0, L_m=3000, i_m_per_m=0.005)
    assert len(alertas) == 3
    assert "Área" in alertas[0] and "Declividade" in alertas[1] and "Comprimento" in alertas[2]

    # Só a área fora da faixa
    alertas = verificar_faixa_kirpich(A_km2=0.001, L_m=500, i_m_per_m=0.05)
    assert len(alertas) == 1 and "Área" in alertas[0]

    assert calcular_tc_kirpich(3000, 0.005) > 0

def test_faixa_kirpich_limites_sao_inclusivos():
    """
    Os valores exatamente nos limites da faixa são aceitos.
    """
    assert verificar_faixa_kirpich(A_km2=0.005, L_m=100, i_m_per_m=0.02) == []
    assert verificar_faixa_kirpich(A_km2=0.45, L_m=1190, i_m_per_m=0.09) == []

def test_faixa_giandotti_dentro():
    """
    Bacia de 500 km²: dentro da faixa (170 a 70.000 km²), sem alertas.
    """
    assert verificar_faixa_giandotti(500) == []

def test_faixa_giandotti_fora():
    """
    Bacia de microdrenagem (0,5 km²) e bacia acima do limite superior geram alerta.
    """
    assert len(verificar_faixa_giandotti(0.5)) == 1
    assert len(verificar_faixa_giandotti(100000)) == 1
    assert calcular_tc_giandotti(0.5, 1, 20) > 0
