# config.py

# Constantes Físicas e de Engenharia
G = 9.81      # Aceleração da gravidade (m/s²)
RHO = 1000.0  # Densidade da água (kg/m³)

# Faixas de aplicabilidade dos métodos de tempo de concentração (mínimo, máximo)
# Fonte: Kirpich (1940) e Giandotti (1934), conforme Silveira (2005), RBRH v.10, p.75-89
KIRPICH_FAIXA_AREA_KM2 = (0.005, 0.45)
KIRPICH_FAIXA_DECLIVIDADE_M_M = (0.02, 0.09)
KIRPICH_FAIXA_COMPRIMENTO_KM = (0.10, 1.19)
GIANDOTTI_FAIXA_AREA_KM2 = (170.0, 70000.0)

# Diâmetros nominais comerciais de tubos de concreto para águas pluviais (mm)
# ABNT NBR 8890:2020 — conferir a lista no texto da norma
DIAMETROS_COMERCIAIS_CONCRETO_MM = [300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1500, 1750, 2000]

# Mapeamento de materiais para coeficiente de Manning (n)
MATERIAIS_MANNING = {
    "Canal de concreto acabado": 0.013,
    "Concreto rústico": 0.017,
    "PVC liso (calha aberta)": 0.009,
    "Terra alisada": 0.022,
    "Terra média": 0.025,
    "Terra irregular": 0.030,
    "Rochoso/encosto natural": 0.035,
    "Vegetação leve": 0.040,
    "Vegetação densa": 0.070,
    "Outro (personalizado)": 0.015,
}
