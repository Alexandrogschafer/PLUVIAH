# manning.py

import math
from config import G, RHO

# --- Funções para Condutos Circulares ---

def q_manning_circular_cheia(d, n, S):
    """Calcula a vazão em um conduto circular sob seção cheia."""
    if d <= 0 or n <= 0 or S <= 0:
        return 0.0
    R = d / 4.0
    A = (math.pi / 4.0) * d**2
    return (1.0 / n) * A * (R ** (2.0 / 3.0)) * (S ** 0.5)

def dimensionar_conduto_circular(Q_projeto, n, S, d_min_m, d_max_m, passo_m):
    """Itera para encontrar o diâmetro mínimo que atende à vazão de projeto."""
    d = d_min_m
    while d <= d_max_m + 1e-9:
        q_est = q_manning_circular_cheia(d, n, S)
        if q_est >= Q_projeto:
            return d, q_est
        d += passo_m
    return None, None

# --- Funções para Canais Abertos ---

def geom_trapezio(b, z, y):
    """Retorna Área (A), Perímetro Molhado (P) e Largura do Topo (T) para seção trapezoidal."""
    if y <= 0: return 0.0, max(b, 0.0), max(b, 0.0)
    A = y * (b + z * y)
    P = b + 2.0 * y * (1.0 + z**2) ** 0.5
    T = b + 2.0 * z * y
    return A, P, T

def manning_Q(A, P, S, n):
    """Calcula a vazão pela fórmula de Manning."""
    if P <= 0 or S <= 0 or n <= 0: return 0.0
    R = A / P
    return (1.0/n) * A * (R ** (2.0/3.0)) * (S ** 0.5)

def froude(Q, A, T):
    """Calcula o número de Froude."""
    if A <= 0 or T <= 0: return float('nan')
    V = Q / A
    D = A / T # Profundidade hidráulica
    denom = (G * D) ** 0.5
    return V / denom if denom > 0 else float('inf')

def tau_medio(R, S):
    """Calcula a tensão de arraste média no fundo."""
    if R <= 0: return 0.0
    return RHO * G * R * S

# --- Funções de Solução Numérica (Bisseção) ---

def bissecao(f, a, b, tol=1e-6, maxit=100):
    """Encontra a raiz de uma função 'f' no intervalo [a, b] pelo método da bisseção."""
    try:
        fa, fb = f(a), f(b)
        if fa * fb > 0: return None
    except (ValueError, TypeError):
        return None
        
    L, Rr = a, b
    for _ in range(maxit):
        m = 0.5 * (L + Rr)
        fm = f(m)
        if abs(fm) < tol or (Rr - L) < tol: return max(m, 0.0)
        if fa * fm < 0: Rr, fb = m, fm
        else: L, fa = m, fm
    return max(0.5 * (L + Rr), 0.0)

def y_normal(Qd, b, z, S, n, y_min=1e-4, y_max=50.0):
    """Calcula a profundidade normal (y) para uma dada vazão (Qd)."""
    def f(y):
        A, P, _ = geom_trapezio(b, z, y)
        return manning_Q(A, P, S, n) - Qd
    return bissecao(f, y_min, y_max)

def y_critico(Qd, b, z, y_min=1e-4, y_max=50.0):
    """Calcula a profundidade crítica (yc) para uma dada vazão (Qd)."""
    def F(y):
        A, _, T = geom_trapezio(b, z, y)
        return froude(Qd, A, T) - 1.0
    return bissecao(F, y_min, y_max)

def b_para_Q(Qd, z, y, S, n, b_min=0.01, b_max=50.0):
    """Calcula a largura da base (b) para uma dada vazão (Qd) e profundidade (y)."""
    def f(b):
        A, P, _ = geom_trapezio(b, z, y)
        return manning_Q(A, P, S, n) - Qd
    return bissecao(f, b_min, b_max)
