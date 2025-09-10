# tests/test_racional.py

import pytest
from racional import calcular_vazao_racional

def test_racional_calculo_correto():
    """
    Verifica o cálculo da vazão com valores fáceis de conferir.
    Q = (C * i * A) / 360
    Se C=1, i=100 mm/h, A=3.6 ha, então Q = (1 * 100 * 3.6) / 360 = 1.0 m³/s
    """
    C = 1.0
    i_mm_h = 100.0
    A_ha = 3.6
    resultado_esperado = 1.0
    
    vazao_calculada = calcular_vazao_racional(C, i_mm_h, A_ha)
    
    assert vazao_calculada == pytest.approx(resultado_esperado)

def test_racional_comportamento_fisico():
    """
    Verifica se, mantendo C e i, uma área maior resulta em uma vazão maior.
    """
    C = 0.8
    i_mm_h = 50.0
    area_menor = 10.0
    area_maior = 20.0
    
    vazao_area_menor = calcular_vazao_racional(C, i_mm_h, area_menor)
    vazao_area_maior = calcular_vazao_racional(C, i_mm_h, area_maior)
    
    assert vazao_area_maior > vazao_area_menor

def test_racional_input_zero():
    """
    Garante que se qualquer entrada for zero, a vazão resultante é zero.
    """
    assert calcular_vazao_racional(0, 100, 10) == 0
    assert calcular_vazao_racional(1, 0, 10) == 0
    assert calcular_vazao_racional(1, 100, 0) == 0
