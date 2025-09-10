# tests/test_manning.py

import pytest
from manning import (
    geom_trapezio,
    manning_Q,
    q_manning_circular_cheia,
    dimensionar_conduto_circular
)

# --- Testes para Canais Abertos (Trapezoidal/Retangular) ---

def test_geom_trapezio_retangular():
    """
    Verifica os cálculos de geometria para um canal retangular (talude z=0).
    """
    b = 2.0  # largura da base
    y = 1.0  # profundidade
    z = 0.0  # talude para canal retangular
    
    A, P, T = geom_trapezio(b, z, y)
    
    # Valores esperados para um retângulo de 2x1
    assert A == pytest.approx(2.0)   # Área = b * y = 2 * 1 = 2
    assert P == pytest.approx(4.0)   # Perímetro molhado = b + 2y = 2 + 2*1 = 4
    assert T == pytest.approx(2.0)   # Largura do topo = b = 2

def test_geom_trapezio_com_talude():
    """
    Verifica os cálculos de geometria para um canal trapezoidal.
    """
    b = 2.0
    y = 1.0
    z = 1.5 # talude 1.5H:1V
    
    A, P, T = geom_trapezio(b, z, y)

    # Valores esperados calculados manualmente
    # A = y * (b + z*y) = 1 * (2 + 1.5*1) = 3.5
    # P = b + 2*y*sqrt(1+z^2) = 2 + 2*1*sqrt(1 + 1.5^2) = 5.6055
    # T = b + 2*z*y = 2 + 2*1.5*1 = 5.0
    assert A == pytest.approx(3.5)
    assert P == pytest.approx(5.6055, rel=1e-4)
    assert T == pytest.approx(5.0)

def test_manning_Q_calculo_correto():
    """
    Verifica se a fórmula de Manning para canais abertos calcula um valor conhecido.
    Este teste usa um exemplo claro e verificável.
    """
    # Usando a geometria retangular do primeiro teste
    A = 2.0
    P = 4.0
    S = 0.001  # Declividade de 0.1%
    n = 0.013  # Manning para concreto
    
    # Q = (1/n) * A * (A/P)^(2/3) * S^(1/2)
    # Q = (1/0.013) * 2 * (2/4)^(2/3) * (0.001)^(1/2) ~= 3.07 m³/s
    q_calculada = manning_Q(A, P, S, n)
    
    assert q_calculada == pytest.approx(3.07, rel=1e-2)

def test_manning_Q_comportamento_fisico_rugosidade():
    """
    Garante que, se o coeficiente de Manning 'n' aumenta (mais rugoso),
    a vazão calculada diminui, como esperado fisicamente.
    Este é o teste de comportamento mencionado pelo seu professor.
    """
    A = 2.0
    P = 4.0
    S = 0.001
    n_liso = 0.013       # Coeficiente menor (canal mais liso)
    n_rugoso = 0.030     # Coeficiente maior (canal mais rugoso)
    
    q_liso = manning_Q(A, P, S, n_liso)
    q_rugoso = manning_Q(A, P, S, n_rugoso)
    
    assert q_rugoso < q_liso

# --- Testes para Condutos Circulares ---

def test_q_manning_circular_cheia_calculo_correto():
    """
    Verifica o cálculo de vazão para um conduto circular de seção cheia.
    """
    d = 0.5    # Diâmetro de 500 mm
    n = 0.013  # Concreto
    S = 0.01   # Declividade de 1%
    
    # Valor esperado calculado manualmente:
    # A = pi*d²/4 ~= 0.19635 m²
    # R = d/4 = 0.125 m
    # Q = (1/0.013) * 0.19635 * (0.125)^(2/3) * (0.01)^(1/2) ~= 0.377 m³/s
    q_calculada = q_manning_circular_cheia(d, n, S)
    
    assert q_calculada == pytest.approx(0.377, rel=1e-2)

def test_dimensionar_conduto_circular_logica():
    """
    Testa a lógica da função de dimensionamento.
    Verifica se a função escolhe o menor diâmetro que satisfaz a vazão de projeto.
    """
    Q_projeto = 0.3  # m³/s
    n = 0.013
    S = 0.01
    
    # Vamos calcular as capacidades para alguns diâmetros
    q_d400 = q_manning_circular_cheia(d=0.4, n=n, S=S) # ~= 0.222 m³/s (Insuficiente)
    q_d500 = q_manning_circular_cheia(d=0.5, n=n, S=S) # ~= 0.377 m³/s (Suficiente)
    q_d600 = q_manning_circular_cheia(d=0.6, n=n, S=S) # ~= 0.578 m³/s (Suficiente, mas não é o mínimo)

    # A função deve retornar o diâmetro de 0.5m (500mm) e sua respectiva vazão
    d_rec, Q_calc = dimensionar_conduto_circular(
        Q_projeto, n, S, d_min_m=0.1, d_max_m=2.0, passo_m=0.1
    )
    
    assert d_rec == pytest.approx(0.5)
    assert Q_calc == pytest.approx(q_d500)

def test_dimensionar_conduto_nao_encontrado():
    """
    Testa o caso em que nenhum diâmetro no intervalo consegue atender à vazão.
    """
    Q_projeto_alto = 100.0  # Vazão muito alta
    n = 0.013
    S = 0.001

    # Com um intervalo de diâmetros pequeno, a função não deve encontrar solução
    d_rec, Q_calc = dimensionar_conduto_circular(
        Q_projeto_alto, n, S, d_min_m=0.1, d_max_m=1.0, passo_m=0.1
    )

    assert d_rec is None
    assert Q_calc is None
