def calcular_vazao_racional(C, i_mm_h, A_ha):
    """Calcula a vazão de projeto pelo Método Racional. Retorna Q em m³/s."""
    if C <= 0 or i_mm_h <= 0 or A_ha <= 0:
        return 0.0
    # Fator de conversão 360 para (mm/h * ha) -> m³/s
    return (C * i_mm_h * A_ha) / 360.0
