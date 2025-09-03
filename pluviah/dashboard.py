# dashboard.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import tempfile
import os
import math
from streamlit_option_menu import option_menu

# --- 1. IMPORTAÇÕES DA LÓGICA MODULARIZADA ---
# Certifique-se de que a estrutura de pastas está correta para estas importações
from data_handler import load_data
from idf import (calculate_annual_maxima, calculate_idf_curves, 
                               calcular_chuva_projeto)
from tc import calcular_tc_kirpich, calcular_tc_giandotti
from racional import calcular_vazao_racional
from manning import (dimensionar_conduto_circular, geom_trapezio, 
                                   manning_Q)
from relatorio import generate_professional_pdf
# A importação de MATERIAIS_MANNING foi removida pois não estava sendo usada na UI
# Se for usar, lembre-se de criar o arquivo pluviah/config.py
# from pluviah.config import MATERIAIS_MANNING

# ==============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL (CSS)
# ==============================================================================
st.set_page_config(
    page_title="PLUVIAH | Análise Pluviométrica e Hidráulica",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css');
    body {
    font-family: 'Poppins', sans-serif;
}
/* Ou, se quiser ser mais específico para o Streamlit sem afetar ícones: */
.stApp {
    font-family: 'Poppins', sans-serif;
}

    :root {
        --primary-color: #56B4E9;
        --background-color: #0F1116;
        --secondary-background-color: #1E2129;
        --text-color: #FAFAFA;
        --light-text-color: #A0A0B0;
        --border-color: #3A3D46;
    }
    .stApp { background-color: var(--background-color); color: var(--text-color); }
    h1, h2, h3 { color: #F8F8F8 !important; font-weight: 600; }
    h2 { border-bottom: 2px solid var(--border-color); padding-bottom: 10px; margin-bottom: 20px; }
    .stMetric, [data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stVerticalBlockBorderWrapper"], .stDataFrame, .stAlert {
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        background-color: var(--secondary-background-color);
        border: 1px solid var(--border-color);
        padding: 20px;
    }
    .stButton>button {
        border-radius: 8px; border: 2px solid var(--primary-color); background-color: var(--primary-color);
        color: var(--background-color); font-weight: 600; transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover { background-color: transparent; color: var(--primary-color); }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNÇÕES COM CACHE (NA CAMADA DE UI)
# ==============================================================================
@st.cache_data
def cached_load_data(uploaded_file):
    return load_data(uploaded_file)

@st.cache_data
def cached_calculate_annual_maxima(_df, duration):
    return calculate_annual_maxima(_df, duration)

@st.cache_data
def cached_calculate_idf_curves(series, duration, trs_np):
    return calculate_idf_curves(series, duration, trs_np)

# ==============================================================================
# 4. INTERFACE DO DASHBOARD
# ==============================================================================

if 'df' not in st.session_state:
    st.session_state['df'] = None

if st.session_state['df'] is None:
    st.title("PLUVIAH | Análise Pluviométrica e Hidráulica")
    st.caption("Uma ferramenta para análise de séries históricas de chuva e geração de curvas Intensidade-Duração-Frequência.")
    st.divider()

    col1, col2 = st.columns([1, 4])
    with col1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png")
    with col2:
        st.header("Bem-vindo ao PLUVIAH!")
        st.markdown("Para começar, **carregue seus dados de chuva horária (.csv)**.")
    
    uploaded_file = st.file_uploader(
        "Carregue seu arquivo CSV", type=["csv"],
        help="O arquivo deve conter colunas como 'datahora' e 'precipitacao'."
    )

    if uploaded_file is not None:
        try:
            with st.spinner("Analisando seu arquivo..."):
                st.session_state['df'] = cached_load_data(uploaded_file)
            st.success(f"Arquivo **{uploaded_file.name}** carregado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            st.session_state['df'] = None

if st.session_state['df'] is not None:
    df = st.session_state['df']
    
    ano_min_disponivel = df.index.year.min()
    ano_max_disponivel = df.index.year.max()
    df_analise = df

    with st.sidebar:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=100)
        st.markdown("<h1 style='text-align: center;'>PLUVIAH</h1>", unsafe_allow_html=True)
        st.divider()

        pagina_selecionada = option_menu(
            menu_title=None,
            options=[
                "Visão Geral", "Máximas Anuais", "Curvas IDF", "Chuva de Projeto", 
                "Tempo de Concentração", "Vazão de Projeto", "Condutos Circulares", 
                "Canais Abertos", "Relatório PDF"
            ],
            icons=[
                "bar-chart-line", "graph-up", "moisture", "cloud-rain-heavy", 
                "stopwatch", "calculator", "arrows-angle-contract", 
                "water", "file-earmark-pdf"
            ],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "var(--primary-color)", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "var(--secondary-background-color)"
                },
                "nav-link-selected": {
                    "background-color": "var(--primary-color)",
                    "color": "var(--background-color)",
                    "font-weight": "600"
                },
            }
        )
    
    if pagina_selecionada == "Visão Geral":
        st.markdown("## <i class='fas fa-chart-bar'></i> Visão Geral dos Dados", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Período Analisado", f"{ano_min_disponivel}–{ano_max_disponivel}")
        col2.metric("Total de Registros", f"{len(df_analise):,}")
        col3.metric("Máximo Horário", f"{df_analise['precipitacao'].max():.1f} mm")

        st.subheader("Série Temporal da Precipitação (Horária)")
        fig_hourly = go.Figure(data=go.Scatter(x=df_analise.index, y=df_analise['precipitacao'],
                                               mode='lines', name='Precipitação Horária',
                                               line=dict(color='#56B4E9', width=1)))
        fig_hourly.update_layout(
            template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Data", yaxis_title="Precipitação (mm)",
            title="Precipitação Horária Registrada"
        )
        st.plotly_chart(fig_hourly, use_container_width=True, config={'displayModeBar': False})
        
        st.subheader("Série Temporal da Precipitação (Agregada)")
        aggregation_level = st.selectbox("Agregar dados por:", ['Diária', 'Mensal', 'Anual'], index=0)
        
        df_plot = df_analise['precipitacao']
        if aggregation_level == 'Diária':
            df_plot = df_plot.resample('D').sum()
        elif aggregation_level == 'Mensal':
            df_plot = df_plot.resample('ME').sum()
        elif aggregation_level == 'Anual':
            df_plot = df_plot.resample('YE').sum()

        fig_serie = px.line(x=df_plot.index, y=df_plot.values, labels={'y': 'Precipitação (mm)', 'x': 'Data'}, title=f"Precipitação Agregada ({aggregation_level})")
        fig_serie.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_serie, use_container_width=True)

    elif pagina_selecionada == "Máximas Anuais":
        st.markdown("## <i class='fas fa-chart-line'></i> Análise de Máximas Anuais", unsafe_allow_html=True)
        duracao_max = st.selectbox("Duração (horas):", [1, 2, 3, 6, 12, 24], key='duracao_maximas')
        
        with st.spinner(f"Calculando máximas para {duracao_max}h..."):
            maximas_anuais = cached_calculate_annual_maxima(df_analise, duracao_max)
        
        if maximas_anuais.empty:
            st.warning("Dados insuficientes para máximas anuais.")
        else:
            df_maximas = maximas_anuais.reset_index()
            df_maximas.columns = ["Ano", "Precipitação Máxima (mm)"]
            
            fig_maximas = px.bar(
                df_maximas, x="Ano", y="Precipitação Máxima (mm)",
                title=f"Máximas Anuais ({duracao_max}h)", text_auto=".1f"
            )
            fig_maximas.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_maximas, use_container_width=True)
            
            with st.expander("Ver dados da tabela"):
                st.dataframe(df_maximas.set_index("Ano"), use_container_width=True)

    elif pagina_selecionada == "Curvas IDF":
        st.markdown("## <i class='fas fa-chart-area'></i> Curvas Intensidade-Duração-Frequência (IDF)", unsafe_allow_html=True)
        duracao_idf = st.selectbox("Duração para ajuste (horas):", [1, 2, 3, 6, 12, 24], key='duracao_idf')
        trs = [2, 5, 10, 25, 50, 100]
        
        with st.spinner(f"Ajustando curvas para {duracao_idf}h..."):
            series_maximas = cached_calculate_annual_maxima(df_analise, duracao_idf)
            df_idf, params_gumbel, params_lp3, gumbel_params_tuple, lp3_params_tuple = cached_calculate_idf_curves(
                series_maximas, duracao_idf, np.array(trs)
            )

        if df_idf is None:
            st.warning("Série curta para ajuste estatístico (mínimo de 5 anos de dados).")
        else:
            st.session_state.update({
                'gumbel_params': gumbel_params_tuple,
                'lp3_params': lp3_params_tuple,
                'duracao_idf_calculada': duracao_idf,
                'df_idf': df_idf,
                'params_gumbel': params_gumbel,
                'params_lp3': params_lp3
            })
            
            fig_idf = go.Figure()
            fig_idf.add_trace(go.Scatter(x=df_idf["TR (anos)"], y=df_idf[f"Gumbel_{duracao_idf}h (mm)"], mode='lines+markers', name='Gumbel'))
            fig_idf.add_trace(go.Scatter(x=df_idf["TR (anos)"], y=df_idf[f"LP3_{duracao_idf}h (mm)"], mode='lines+markers', name='Log-Pearson III'))
            fig_idf.update_layout(
                title=f"Precipitação Estimada vs. Período de Retorno (Duração: {duracao_idf}h)",
                xaxis_title="Período de Retorno (anos)", yaxis_title="Precipitação (mm)",
                xaxis_type="log", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_idf, use_container_width=True)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig_idf.write_image(tmpfile.name)
                st.session_state['grafico_path'] = tmpfile.name
            
            st.dataframe(df_idf.style.format("{:.2f}"))

    elif pagina_selecionada == "Chuva de Projeto":
        st.markdown("## <i class='fas fa-cloud-showers-heavy'></i> Cálculo de Chuva de Projeto", unsafe_allow_html=True)
        tr_tab4 = st.number_input("Período de Retorno (anos):", min_value=1, step=1, value=10)
        dur_tab4 = st.number_input("Duração da Chuva (horas):", min_value=0.1, step=0.1, value=1.0)
        metodo_tab4 = st.radio("Método de Cálculo:", ["Gumbel", "Log-Pearson III"])

        if st.button("Calcular Chuva de Projeto", key="btn_calc_chuva"):
            gumbel_params = st.session_state.get('gumbel_params')
            lp3_params = st.session_state.get('lp3_params')

            if (metodo_tab4 == "Gumbel" and not gumbel_params) or \
               (metodo_tab4 == "Log-Pearson III" and not lp3_params):
                st.error("Parâmetros não encontrados. Por favor, calcule as Curvas IDF na página anterior primeiro.")
            else:
                try:
                    chuva_proj = calcular_chuva_projeto(
                        tr=tr_tab4, metodo=metodo_tab4,
                        gumbel_params=gumbel_params, lp3_params=lp3_params
                    )
                    intensidade_proj = chuva_proj / dur_tab4 if dur_tab4 > 0 else 0
                    st.session_state['intensidade_proj_result'] = intensidade_proj
                    st.metric("Intensidade de Projeto (mm/h)", f"{intensidade_proj:.2f}")
                except Exception as e:
                    st.error(f"Ocorreu um erro no cálculo: {e}")

    elif pagina_selecionada == "Tempo de Concentração":
        st.markdown("## <i class='fas fa-stopwatch'></i> Tempo de Concentração", unsafe_allow_html=True)
        metodo_tc = st.selectbox("Selecione o método de cálculo:", ["Kirpich", "Giandotti"])

        if metodo_tc == "Kirpich":
            L_kirpich = st.number_input("Comprimento do curso d'água (m)", min_value=1.0, value=500.0)
            i_kirpich = st.number_input("Declividade média (m/m)", min_value=0.001, value=0.02, format="%.3f")
            tc_min = calcular_tc_kirpich(L_kirpich, i_kirpich)
            st.success(f"Tempo de concentração (Kirpich): **{tc_min:.2f} minutos**")
            st.session_state["tc_min"] = tc_min
        elif metodo_tc == "Giandotti":
            A_giandotti = st.number_input("Área da bacia (km²)", min_value=0.01, value=0.50)
            L_giandotti = st.number_input("Comprimento do percurso (km)", min_value=0.10, value=1.00)
            Hmax = st.number_input("Cota máxima da bacia (m)", value=120.0)
            Hmin = st.number_input("Cota mínima da bacia (m)", value=100.0)
            deltaH = Hmax - Hmin
            if deltaH > 0:
                tc_min = calcular_tc_giandotti(A_giandotti, L_giandotti, deltaH)
                st.success(f"Tempo de concentração (Giandotti): **{tc_min:.2f} minutos**")
                st.session_state["tc_min"] = tc_min
            else:
                st.warning("A cota máxima deve ser maior que a mínima.")
                
    elif pagina_selecionada == "Vazão de Projeto":
        st.markdown("## <i class='fas fa-calculator'></i> Vazão de Projeto – Método Racional", unsafe_allow_html=True)
        intensidade_chuva = st.session_state.get("intensidade_proj_result")
        C = st.number_input("Coeficiente de escoamento (C)", 0.1, 1.0, 0.6)
        A = st.number_input("Área de contribuição (ha)", min_value=0.01, value=5.0)
        
        if intensidade_chuva:
            Q = calcular_vazao_racional(C, intensidade_chuva, A)
            st.success(f"**Vazão de projeto estimada: {Q:.3f} m³/s**")
            st.session_state["q_projeto"] = Q
        else:
            st.warning("Calcule a intensidade da chuva na página 'Chuva de Projeto'.")

    elif pagina_selecionada == "Condutos Circulares":
        st.markdown("## <i class='fas fa-arrows-left-right-to-line'></i> Dimensionamento de Condutos – Manning", unsafe_allow_html=True)
        Q = st.session_state.get("q_projeto")
        if not Q:
            Q = st.number_input("Informe manualmente Q (m³/s)", min_value=0.0, value=0.0, key="q_manual_circ")

        n = st.number_input("Coeficiente de Manning (n)", min_value=0.010, value=0.013, format="%.3f", key="n_manning_circ")
        S = st.number_input("Declividade do conduto S (m/m)", min_value=0.0001, value=0.0100, format="%.4f", key="s_manning_circ")
        
        if Q and Q > 0:
            d_rec, Q_calc = dimensionar_conduto_circular(Q, n, S, d_min_m=0.05, d_max_m=3.0, passo_m=0.01)
            if d_rec:
                st.success(f"**Diâmetro mínimo recomendado: {d_rec:.3f} m**")
                st.metric("Vazão de capacidade do conduto", f"{Q_calc:.3f} m³/s")
            else:
                st.error("Nenhum diâmetro no intervalo padrão atendeu à vazão de projeto.")
        else:
            st.info("Aguardando a definição da vazão de projeto.")

    elif pagina_selecionada == "Canais Abertos":
        st.markdown("## <i class='fas fa-water'></i> Canais Abertos (Manning)", unsafe_allow_html=True)
        Q = st.session_state.get("q_projeto")
        if not Q:
            Q = st.number_input("Informe manualmente Q (m³/s)", min_value=0.0, value=0.0, key="q_manual_canal")

        b = st.number_input("Largura da base b (m)", min_value=0.0, value=1.0)
        y = st.number_input("Profundidade y (m)", min_value=0.0, value=0.5)
        z = st.number_input("Talude z (H:V)", min_value=0.0, value=1.0)
        n_canal = st.number_input("Manning n", min_value=0.005, value=0.015, format="%.3f", key="n_canal")
        S_canal = st.number_input("Declividade S (m/m)", min_value=0.0001, value=0.001, format="%.4f", key="s_canal")

        A, P, T = geom_trapezio(b, z, y)
        Q_calc_canal = manning_Q(A, P, S_canal, n_canal)
        st.metric("Capacidade do canal (m³/s)", f"{Q_calc_canal:.3f}")

    elif pagina_selecionada == "Relatório PDF":
        st.markdown("## <i class='fas fa-file-alt'></i> Relatório em PDF", unsafe_allow_html=True)
        if 'df_idf' in st.session_state and 'grafico_path' in st.session_state:
            if st.button("Gerar Relatório PDF", key="btn_pdf"):
                with st.spinner("Gerando relatório..."):
                    pdf_obj = generate_professional_pdf(
                        st.session_state['df_idf'],
                        st.session_state['grafico_path'],
                        st.session_state['duracao_idf_calculada'],
                        st.session_state['params_gumbel'],
                        st.session_state['params_lp3']
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        pdf_obj.output(tmp.name)
                        with open(tmp.name, "rb") as f:
                            st.download_button("Baixar Relatório", f.read(), f"Relatorio_IDF.pdf", "application/pdf")
        else:
            st.warning("Calcule uma curva IDF primeiro para gerar o relatório.")
