# config.py

# Constantes Físicas e de Engenharia
G = 9.81      # Aceleração da gravidade (m/s²)
RHO = 1000.0  # Densidade da água (kg/m³)

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
