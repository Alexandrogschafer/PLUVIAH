from config import (
    KIRPICH_FAIXA_AREA_KM2, KIRPICH_FAIXA_DECLIVIDADE_M_M, KIRPICH_FAIXA_COMPRIMENTO_KM,
    GIANDOTTI_FAIXA_AREA_KM2,
)

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

def _fora_da_faixa(valor, faixa):
    minimo, maximo = faixa
    return valor < minimo or valor > maximo

def verificar_faixa_kirpich(A_km2, L_m, i_m_per_m):
    """
    Verifica se a bacia esta na faixa de aplicabilidade do metodo de Kirpich (config.py).
    Retorna uma lista de alertas (vazia se tudo estiver dentro da faixa); nao bloqueia o calculo.
    """
    alertas = []
    if _fora_da_faixa(A_km2, KIRPICH_FAIXA_AREA_KM2):
        alertas.append(
            f"Área de {A_km2:g} km² fora da faixa de aplicabilidade "
            f"({KIRPICH_FAIXA_AREA_KM2[0]:g} a {KIRPICH_FAIXA_AREA_KM2[1]:g} km²)."
        )
    if _fora_da_faixa(i_m_per_m, KIRPICH_FAIXA_DECLIVIDADE_M_M):
        alertas.append(
            f"Declividade de {i_m_per_m:g} m/m fora da faixa de aplicabilidade "
            f"({KIRPICH_FAIXA_DECLIVIDADE_M_M[0]:g} a {KIRPICH_FAIXA_DECLIVIDADE_M_M[1]:g} m/m)."
        )
    L_km = L_m / 1000.0
    if _fora_da_faixa(L_km, KIRPICH_FAIXA_COMPRIMENTO_KM):
        alertas.append(
            f"Comprimento de {L_km:g} km fora da faixa de aplicabilidade "
            f"({KIRPICH_FAIXA_COMPRIMENTO_KM[0]:g} a {KIRPICH_FAIXA_COMPRIMENTO_KM[1]:g} km)."
        )
    return alertas

def verificar_faixa_giandotti(A_km2):
    """
    Verifica se a bacia esta na faixa de aplicabilidade do metodo de Giandotti (config.py).
    Retorna uma lista de alertas (vazia se estiver dentro da faixa); nao bloqueia o calculo.
    """
    alertas = []
    if _fora_da_faixa(A_km2, GIANDOTTI_FAIXA_AREA_KM2):
        alertas.append(
            f"Área de {A_km2:g} km² fora da faixa de aplicabilidade "
            f"({GIANDOTTI_FAIXA_AREA_KM2[0]:g} a {GIANDOTTI_FAIXA_AREA_KM2[1]:g} km²)."
        )
    return alertas
