# tests/test_manning.py

import math
import pytest
from config import DIAMETROS_COMERCIAIS_CONCRETO_MM
from manning import (
    geom_trapezio,
    manning_Q,
    q_manning_circular_cheia,
    dimensionar_conduto_circular,
    diametro_teorico_circular,
    geom_circular_parcial,
    q_manning_circular_parcial,
    razao_enchimento_conduto_circular,
    froude,
    y_normal,
    y_critico,
    b_para_Q,
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
    Verifica se a função escolhe o menor diâmetro comercial que satisfaz a vazão de projeto.
    """
    Q_projeto = 0.3  # m³/s
    n = 0.013
    S = 0.01

    # Capacidades a seção cheia dos diâmetros comerciais vizinhos
    q_d400 = q_manning_circular_cheia(d=0.4, n=n, S=S) # ~= 0.208 m³/s (Insuficiente)
    q_d500 = q_manning_circular_cheia(d=0.5, n=n, S=S) # ~= 0.377 m³/s (Suficiente)
    assert q_d400 < Q_projeto < q_d500

    # A função deve retornar o DN 500 e sua respectiva vazão de capacidade
    dn_mm, Q_calc = dimensionar_conduto_circular(Q_projeto, n, S)

    assert dn_mm == 500
    assert Q_calc == pytest.approx(q_d500)

def test_dimensionar_conduto_so_retorna_diametros_da_serie_comercial():
    """Para qualquer vazão atendida, o diâmetro adotado pertence à série comercial de config.py."""
    for Q_projeto in (0.01, 0.2, 0.9, 2.5, 6.0, 14.0):
        dn_mm, Q_calc = dimensionar_conduto_circular(Q_projeto, n=0.013, S=0.01)
        assert dn_mm in DIAMETROS_COMERCIAIS_CONCRETO_MM
        assert Q_calc >= Q_projeto

def test_dimensionar_conduto_respeita_diametro_minimo():
    """Vazão pequena: adota o diâmetro mínimo de projeto (padrão 300 mm, configurável)."""
    assert dimensionar_conduto_circular(0.01, 0.013, 0.01)[0] == 300
    assert dimensionar_conduto_circular(0.01, 0.013, 0.01, d_min_mm=600)[0] == 600

def test_dimensionar_conduto_serie_personalizada():
    """A série de diâmetros é um parâmetro: com outra lista, a escolha muda."""
    dn_mm, _ = dimensionar_conduto_circular(0.3, 0.013, 0.01, diametros_mm=[400, 600, 800])
    assert dn_mm == 600

def test_dimensionar_conduto_nao_encontrado():
    """
    Testa o caso em que a vazão excede a capacidade do maior diâmetro da série:
    a função sinaliza com (None, None) em vez de devolver um diâmetro insuficiente.
    """
    Q_projeto_alto = 100.0  # Vazão muito alta
    n = 0.013
    S = 0.001

    q_maior_dn = q_manning_circular_cheia(max(DIAMETROS_COMERCIAIS_CONCRETO_MM) / 1000.0, n, S)
    assert q_maior_dn < Q_projeto_alto

    dn_mm, Q_calc = dimensionar_conduto_circular(Q_projeto_alto, n, S)

    assert dn_mm is None
    assert Q_calc is None

def test_dimensionar_conduto_sobe_o_dn_para_atender_o_enchimento():
    """
    Q=0.37 m³/s, n=0.013, S=0.01: o DN 500 tem capacidade (0.378 m³/s), mas trabalha com
    y/D ~= 0.80. Com critério de 0.85 ele serve; com critério de 0.75 é preciso o DN 600.
    """
    n, S = 0.013, 0.01
    assert dimensionar_conduto_circular(0.37, n, S, criterio_yD=0.85)[0] == 500
    assert dimensionar_conduto_circular(0.37, n, S, criterio_yD=0.75)[0] == 600
    # Sem o critério de enchimento, vale só a capacidade a seção cheia
    assert dimensionar_conduto_circular(0.37, n, S, criterio_yD=None)[0] == 500

def test_dimensionar_conduto_resultado_atende_as_duas_condicoes():
    """O DN adotado sempre tem capacidade >= Q e y/D <= critério, e o DN anterior da série falha em uma delas."""
    n, S = 0.013, 0.01
    serie = DIAMETROS_COMERCIAIS_CONCRETO_MM
    for Q_projeto in (0.05, 0.2, 0.37, 1.0, 3.0, 8.0):
        for criterio in (0.5, 0.75, 0.85):
            dn_mm, Q_calc = dimensionar_conduto_circular(Q_projeto, n, S, criterio_yD=criterio)
            razao, dentro = razao_enchimento_conduto_circular(Q_projeto, dn_mm / 1000.0, n, S, criterio_max=criterio)
            assert Q_calc >= Q_projeto
            assert dentro and razao <= criterio

            indice = serie.index(dn_mm)
            if indice > 0:
                d_anterior = serie[indice - 1] / 1000.0
                tem_capacidade = q_manning_circular_cheia(d_anterior, n, S) >= Q_projeto
                _, dentro_anterior = razao_enchimento_conduto_circular(Q_projeto, d_anterior, n, S, criterio_max=criterio)
                assert not (tem_capacidade and dentro_anterior)

def test_dimensionar_conduto_enchimento_nao_atendido_por_nenhum_dn():
    """
    Q=14 m³/s cabe no DN 2000 a seção cheia (15.2 m³/s), mas com y/D ~= 0.76.
    Com critério de 0.75 nenhum diâmetro da série atende: retorna (None, None).
    """
    assert dimensionar_conduto_circular(14.0, 0.013, 0.01, criterio_yD=0.85)[0] == 2000
    assert dimensionar_conduto_circular(14.0, 0.013, 0.01, criterio_yD=0.75) == (None, None)

def test_diametro_teorico_circular_valor_conhecido():
    """
    Q=0.3 m³/s, n=0.013, S=0.01:
    d = (4^(5/3) * 0.013 * 0.3 / (pi * 0.1))^(3/8) = (0.12513)^(0.375) = 0.4587 m,
    que fica entre o DN 400 e o DN 500 — coerente com o DN 500 adotado.
    """
    d_teorico = diametro_teorico_circular(0.3, 0.013, 0.01)
    assert d_teorico == pytest.approx(0.4587, abs=1e-4)

def test_diametro_teorico_circular_conduz_exatamente_a_vazao():
    """No diâmetro teórico, a capacidade a seção cheia é igual à vazão de projeto."""
    for Q_projeto in (0.05, 0.3, 4.0):
        d_teorico = diametro_teorico_circular(Q_projeto, 0.015, 0.004)
        assert q_manning_circular_cheia(d_teorico, 0.015, 0.004) == pytest.approx(Q_projeto)

def test_diametro_teorico_circular_entrada_invalida():
    """Vazão, rugosidade ou declividade não positivas retornam 0."""
    assert diametro_teorico_circular(0.0, 0.013, 0.01) == 0.0
    assert diametro_teorico_circular(0.3, 0.013, 0.0) == 0.0

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


# --- Testes para as solucoes numericas (bissecao) em canais abertos ---

def test_y_normal_canal_retangular_valor_conhecido():
    """
    Canal retangular b=2 m, S=0.001, n=0.013 com y=1 m:
    A=2, P=4, R=0.5 -> Q = (1/0.013) * 2 * 0.5^(2/3) * 0.001^0.5 = 3.0648 m3/s.
    Logo, a profundidade normal para Q=3.0648 deve ser 1.0 m.
    """
    yn = y_normal(3.0648, b=2.0, z=0.0, S=0.001, n=0.013)
    assert yn == pytest.approx(1.0, abs=1e-4)

def test_y_normal_canal_trapezoidal_satisfaz_manning():
    """A profundidade normal encontrada deve reproduzir a vazao de projeto pela formula de Manning."""
    Qd, b, z, S, n = 10.0, 3.0, 1.5, 0.0005, 0.025
    yn = y_normal(Qd, b, z, S, n)
    A, P, _ = geom_trapezio(b, z, yn)
    assert manning_Q(A, P, S, n) == pytest.approx(Qd, rel=1e-4)

def test_y_normal_comportamento_fisico():
    """Maior vazao exige maior profundidade; maior declividade reduz a profundidade."""
    y_base = y_normal(5.0, 2.0, 1.0, 0.001, 0.013)
    assert y_normal(10.0, 2.0, 1.0, 0.001, 0.013) > y_base
    assert y_normal(5.0, 2.0, 1.0, 0.01, 0.013) < y_base

def test_y_normal_vazao_fora_do_intervalo_de_busca():
    """Se a vazao nao pode ser atingida dentro de [y_min, y_max], nao ha raiz: retorna None."""
    assert y_normal(1e9, 2.0, 0.0, 0.001, 0.013) is None

def test_y_critico_canal_retangular_valor_conhecido():
    """
    Em canal retangular a profundidade critica tem solucao fechada: yc = (q^2 / g)^(1/3), q = Q/b.
    Q=5, b=2 -> q=2.5 -> yc = (6.25 / 9.81)^(1/3) = 0.8605 m.
    """
    yc = y_critico(5.0, b=2.0, z=0.0)
    assert yc == pytest.approx(0.8605, abs=1e-4)

def test_y_critico_canal_trapezoidal_froude_unitario():
    """Na profundidade critica o numero de Froude deve ser 1."""
    Qd, b, z = 12.0, 3.0, 2.0
    yc = y_critico(Qd, b, z)
    A, _, T = geom_trapezio(b, z, yc)
    assert froude(Qd, A, T) == pytest.approx(1.0, abs=1e-4)

def test_y_critico_independe_de_declividade_e_cresce_com_a_vazao():
    """A profundidade critica depende so da vazao e da geometria, e cresce com a vazao."""
    assert y_critico(10.0, 2.0, 1.0) > y_critico(5.0, 2.0, 1.0)

def test_b_para_Q_canal_retangular_valor_conhecido():
    """Mesmo caso de referencia do y_normal: Q=3.0648, y=1, S=0.001, n=0.013 -> b=2.0 m."""
    b = b_para_Q(3.0648, z=0.0, y=1.0, S=0.001, n=0.013)
    assert b == pytest.approx(2.0, abs=1e-4)

def test_b_para_Q_e_inverso_de_y_normal():
    """A largura encontrada para (Q, y) deve devolver a mesma profundidade em y_normal."""
    Qd, z, y, S, n = 8.0, 1.5, 1.2, 0.002, 0.017
    b = b_para_Q(Qd, z, y, S, n)
    assert y_normal(Qd, b, z, S, n) == pytest.approx(y, abs=1e-4)

def test_b_para_Q_vazao_fora_do_intervalo_de_busca():
    """
    Canal triangular-limite (b -> b_min) com z=1.5 e y=1.2 ja conduz mais que 0.01 m3/s,
    entao nao existe largura em [b_min, b_max] para essa vazao: retorna None.
    """
    assert b_para_Q(0.01, z=1.5, y=1.2, S=0.002, n=0.017) is None
