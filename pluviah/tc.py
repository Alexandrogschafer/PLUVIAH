def calcular_tc_kirpich(L_m, i_m_per_m):
    """Calcula o Tempo de Concentracao pelo método de Kirpich. Retorna Tc em minutos."""
    if L_m <= 0 or i_m_per_m <= 0:
        return 0.0
    return 0.0195 * (L_m ** 0.77) * (i_m_per_m ** -0.385)

def calcular_tc_giandotti(A_km2, L_km, H_m):
    """
    Calcula o Tempo de Concentracao pelo metodo de Giandotti. Retorna Tc em minutos.

    Tc (h) = (4 * sqrt(A) + 1.5 * L) / (0.8 * sqrt(H))

    A_km2: area da bacia (km2); L_km: comprimento do talvegue principal (km);
    H_m: altitude media da bacia menos a cota do exutorio (m).
    """
    if A_km2 <= 0 or L_km <= 0 or H_m <= 0:
        return 0.0
    tc_h = (4 * A_km2 ** 0.5 + 1.5 * L_km) / (0.8 * H_m ** 0.5)
    return tc_h * 60.0
