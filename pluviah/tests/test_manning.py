# tests/test_manning.py

import math
import pytest
from manning import (
    geom_trapezio,
    manning_Q,
    q_manning_circular_cheia,
    dimensionar_conduto_circular,
    geom_circular_parcial,
    q_manning_circular_parcial,
    razao_enchimento_conduto_circular,
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

# --- Testes para Condutos Circulares Parcialmente Cheios (Razão de Enchimento) ---

def test_geom_circular_parcial_meia_secao():
    """
    Verifica a geometria de um conduto circular à meia-seção (y = D/2).
    Valores de referência (D=0.5 m):
      theta = 2*acos(1 - 2*(D/2)/D) = 2*acos(0) = pi
      A = (D²/8)*(pi - sin(pi)) = (D²/8)*pi ≈ 0.098175 m²
      P = (pi/2)*D ≈ 0.785398 m
    """
    d = 0.5
    A, P = geom_circular_parcial(d, y=d / 2)

    assert A == pytest.approx((d**2 / 8.0) * math.pi, rel=1e-6)
    assert P == pytest.approx((math.pi / 2.0) * d, rel=1e-6)

    # À meia-seção, o raio hidráulico R = A/P coincide com o da seção plena (D/4),
    # já que tanto a área quanto o perímetro molhado são exatamente metade dos da seção cheia.
    assert A / P == pytest.approx(d / 4.0, rel=1e-6)

def test_q_manning_circular_parcial_meia_secao_e_metade_da_vazao_cheia():
    """
    Como o raio hidráulico à meia-seção (y=D/2) é igual ao da seção plena, e a área
    é exatamente metade, a vazão de Manning à meia-seção deve ser exatamente metade
    da vazão em seção plena (mesmo n, S e R).
    """
    d, n, S = 0.5, 0.013, 0.01

    q_cheia = q_manning_circular_cheia(d, n, S)
    q_meia = q_manning_circular_parcial(d / 2, d, n, S)

    assert q_meia == pytest.approx(q_cheia / 2.0, rel=1e-6)

def test_razao_enchimento_conduto_circular_calculo_correto():
    """
    Para uma vazão de projeto igual à metade da capacidade plena, a razão de
    enchimento (y/D) deve ser 0.5 (ver teste da meia-seção acima) e estar dentro
    do critério padrão de projeto (y/D <= 0.85).
    """
    d, n, S = 0.5, 0.013, 0.01
    Q_full = q_manning_circular_cheia(d, n, S)

    razao_yD, dentro_criterio = razao_enchimento_conduto_circular(Q_full / 2.0, d, n, S)

    assert razao_yD == pytest.approx(0.5, rel=1e-3)
    assert dentro_criterio is True

def test_razao_enchimento_comportamento_fisico():
    """
    Garante que, mantendo o diâmetro fixo, uma vazão de projeto maior resulta em
    uma razão de enchimento (y/D) maior — comportamento físico esperado.
    """
    d, n, S = 0.5, 0.013, 0.01
    Q_full = q_manning_circular_cheia(d, n, S)

    razao_baixa, _ = razao_enchimento_conduto_circular(Q_full * 0.3, d, n, S)
    razao_alta, _ = razao_enchimento_conduto_circular(Q_full * 0.9, d, n, S)

    assert razao_alta > razao_baixa

def test_razao_enchimento_acima_do_criterio_configuravel():
    """
    Perto da capacidade plena (Q -> Qfull), a razão de enchimento no ramo ascendente
    tende a ~0.82 (valor clássico de hidráulica de condutos circulares). Com um
    critério de projeto mais rígido (0.75), isso deve ser sinalizado como fora do critério,
    embora o critério padrão (0.85) ainda seja atendido.
    """
    d, n, S = 0.5, 0.013, 0.01
    Q_full = q_manning_circular_cheia(d, n, S)
    Q_quase_cheio = Q_full * 0.999

    razao_yD, dentro_padrao = razao_enchimento_conduto_circular(Q_quase_cheio, d, n, S)
    _, dentro_rigido = razao_enchimento_conduto_circular(Q_quase_cheio, d, n, S, criterio_max=0.75)

    assert razao_yD == pytest.approx(0.82, abs=0.01)
    assert dentro_padrao is True
    assert dentro_rigido is False

def test_razao_enchimento_vazao_acima_da_capacidade_plena():
    """
    Se a vazão de projeto excede a capacidade da seção plena, não existe profundidade
    y/D <= 1 que a atenda: a função deve sinalizar isso (razão None, fora do critério).
    """
    d, n, S = 0.5, 0.013, 0.01
    Q_full = q_manning_circular_cheia(d, n, S)

    razao_yD, dentro_criterio = razao_enchimento_conduto_circular(Q_full * 1.5, d, n, S)

    assert razao_yD is None
    assert dentro_criterio is False
