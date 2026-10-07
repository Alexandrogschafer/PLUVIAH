def calcular_tc_kirpich(L_m, i_m_per_m):
    """Calcula o Tempo de Concentracao pelo método de Kirpich. Retorna Tc em minutos."""
    if L_m <= 0 or i_m_per_m <= 0:
        return 0.0
    return 0.0195 * (L_m ** 0.77) * (i_m_per_m ** -0.385)

def calcular_tc_giandotti(A_km2, L_km, deltaH_m):
    """
    Calcula o Tempo de Concentracao pelo meetodo de Giandotti. Retorna Tc em minutos.
    NOTA: Esta implementacao e uma variante: tc_h = (4 * A + 1.5 * L) / (0.8 * deltaH).
    A forma classica usa raizes: (4 * sqrt(A) + 1.5 * L) / (0.8 * sqrt(Hm)), com Hm = altura
    media da bacia acima do exutorio. Os resultados diferem; ver docs/manual.md.
    """
    if A_km2 <= 0 or L_km <= 0 or deltaH_m <= 0:
        return 0.0
    tc_h = (4 * A_km2 + 1.5 * L_km) / (0.8 * deltaH_m)
    return tc_h * 60.0
