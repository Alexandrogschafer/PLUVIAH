def calcular_vazao_racional(C, i_mm_h, A_ha):
    """Calcula a vazao de projeto pelo Metodo Racional. Retorna Q em m³/s."""
    if C <= 0 or i_mm_h <= 0 or A_ha <= 0:
        return 0.0
    # Fator de conversao 360 para (mm/h * ha) -> m³/s
    return (C * i_mm_h * A_ha) / 360.0
