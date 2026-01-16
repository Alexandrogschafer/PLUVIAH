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
from data_handler import load_data
from idf import calculate_annual_maxima, calculate_idf_curves, calcular_chuva_projeto
from tc import calcular_tc_kirpich, calcular_tc_giandotti
from racional import calcular_vazao_racional
from manning import (
    dimensionar_conduto_circular, geom_trapezio, manning_Q, froude, tau_medio,
    y_normal, y_critico, b_para_Q
)
from relatorio import gerar_pdf_bytes
from config import MATERIAIS_MANNING, G, RHO


# =============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA E ESTILO VISUAL (CSS)
# ==============================================================================
st.set_page_config(
    page_title="PLUVIAH | Análise Pluviométrica e Hidráulica",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css');
    body, .stApp { font-family: 'Poppins', sans-serif; }
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
    .stMetric, [data-testid="stMetric"], [data-testid="stExpander"], .stDataFrame, .stAlert, [data-testid="stVerticalBlockBorderWrapper"] {
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
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. FUNÇÕES COM CACHE
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
# 5. INTERFACE DO DASHBOARD
# ==============================================================================

st.title("PLUVIAH | Análise Pluviométrica e Hidráulica")
st.caption("Uma ferramenta para análise de séries históricas de chuva, geração de curvas IDF e dimensionamento hidráulico.")
st.divider()

# --- LÓGICA DE ESTADO: SEM DADOS CARREGADOS ---
if 'df' not in st.session_state or st.session_state.df is None:
    st.info("Para começar carregue um arquivo com dados de chuva.")
    
    pagina_selecionada = "Visão Geral"
    
    with st.sidebar:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=100)
        st.markdown("<h1 style='text-align: center;'>PLUVIAH</h1>", unsafe_allow_html=True)
        st.divider()

# --- LÓGICA DE ESTADO: DADOS CARREGADOS ---
else:
    with st.sidebar:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=100)
        st.markdown("<h1 style='text-align: center;'>PLUVIAH</h1>", unsafe_allow_html=True)
        st.divider()

        pagina_selecionada = option_menu(
            menu_title=None,
            options=[
                "Visão Geral", "Curvas IDF", "Chuva de Projeto",
                "Tempo de Concentração", "Vazão de Projeto", "Condutos Circulares",
                "Canais Abertos", "Relatório PDF"
            ],
            icons=[
                "bar-chart-line", "moisture", "cloud-rain-heavy",
                "stopwatch", "calculator", "arrows-angle-contract",
                "water", "file-earmark-pdf"
            ],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "var(--primary-color)", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "var(--secondary-background-color)"},
                "nav-link-selected": {"background-color": "var(--primary-color)", "color": "var(--background-color)", "font-weight": "600"},
            }
        )

# --- RENDERIZAÇÃO DAS PÁGINAS ---
# --- ABA 1: VISÃO GERAL (COM UPLOADER CONDICIONAL) ---
if pagina_selecionada == "Visão Geral":
    
    if 'df' not in st.session_state or st.session_state.df is None:
        st.markdown("### <i class='fas fa-upload'></i> Carregar Dados de Chuva", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Selecione seu arquivo CSV", type=["csv"],
            help="O arquivo deve conter colunas como 'datahora' e 'precipitacao'."
        )
        if uploaded_file is not None:
            try:
                with st.spinner("Analisando seu arquivo..."):
                    st.session_state['df'] = cached_load_data(uploaded_file)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                st.session_state['df'] = None
    
    else:
        df = st.session_state.df
        ano_min_disponivel = df.index.year.min()
        ano_max_disponivel = df.index.year.max()
        df_analise = df

        _, col_btn = st.columns([5, 1])
        with col_btn:
            if st.button("Alterar Arquivo"):
                st.session_state.clear()
                st.rerun()

        st.markdown("## <i class='fas fa-chart-bar'></i> Visão Geral e Máximas Anuais", unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Período Analisado", f"{ano_min_disponivel}–{ano_max_disponivel}")
        col2.metric("Total de Registros", f"{len(df_analise):,}")
        col3.metric("Máximo Horário", f"{df_analise['precipitacao'].max():.1f} mm")

        st.subheader("Série Temporal da Precipitação (Horária)")
        fig_hourly = go.Figure(data=go.Scatter(x=df_analise.index, y=df_analise['precipitacao'],
                                              mode='lines', name='Precipitação Horária',
                                              line=dict(color='#56B4E9', width=1)))
        fig_hourly.update_layout(
            template="plotly_dark", height=350,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Data", yaxis_title="Precipitação (mm)",
            title="Precipitação Horária Registrada"
        )
        st.plotly_chart(fig_hourly, use_container_width=True, config={'displayModeBar': False})

        st.subheader("Série Temporal da Precipitação (Agregada)")
        aggregation_level = st.selectbox("Agregar dados por:", ['Diária', 'Mensal', 'Anual'], index=0)

        df_plot = df_analise['precipitacao']
        if aggregation_level == 'Diária': df_plot = df_plot.resample('D').sum()
        elif aggregation_level == 'Mensal': df_plot = df_plot.resample('ME').sum()
        elif aggregation_level == 'Anual': df_plot = df_plot.resample('YE').sum()

        fig_serie = px.line(x=df_plot.index, y=df_plot.values, labels={'y': 'Precipitação (mm)', 'x': 'Data'}, title=f"Precipitação Agregada ({aggregation_level})")
        fig_serie.update_layout(template="plotly_dark", height=400, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_serie, use_container_width=True)
        
        st.divider()
        
        st.subheader("Análise de Máximas Anuais")
        duracao_max = st.selectbox("Selecione a duração para análise (horas):", [1, 2, 3, 6, 12, 24], key='duracao_maximas')
        
        with st.spinner(f"Calculando máximas para {duracao_max}h..."):
            maximas_anuais = cached_calculate_annual_maxima(df_analise, duracao_max)

        if maximas_anuais.empty:
            st.warning("Dados insuficientes para calcular as máximas anuais.")
        else:
            df_maximas = maximas_anuais.reset_index()
            df_maximas.columns = ["Ano", "Precipitação Máxima (mm)"]
            
            fig_maximas = px.bar(
                df_maximas, x="Ano", y="Precipitação Máxima (mm)",
                title=f"Precipitações Máximas Anuais para Duração de {duracao_max}h", text_auto=".1f"
            )
            fig_maximas.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_maximas.update_traces(marker_color='#56B4E9', textposition='outside')
            st.plotly_chart(fig_maximas, use_container_width=True)
            
            with st.expander("Ver dados da tabela de máximas anuais"):
                st.dataframe(df_maximas.set_index("Ano"), use_container_width=True)

# --- ABA 2: CURVAS IDF ---
elif pagina_selecionada == "Curvas IDF":
    st.markdown("## <i class='fas fa-chart-area'></i> Curvas Intensidade-Duração-Frequência (IDF)", unsafe_allow_html=True)
    
    duracao_idf = st.selectbox("Duração para ajuste (horas):", [1, 2, 3, 6, 12, 24], key='duracao_idf')
    
    if st.button("Calcular Curvas IDF e Ajuste Estatístico"):
        trs = np.array([2, 5, 10, 25, 50, 100])
        with st.spinner(f"Ajustando curvas para {duracao_idf}h..."):
            series_maximas = cached_calculate_annual_maxima(st.session_state.df, duracao_idf)
            results = cached_calculate_idf_curves(series_maximas, duracao_idf, trs)
            st.session_state['idf_results'] = results
            st.session_state['duracao_idf_calculada'] = duracao_idf
    
    if st.session_state.get('idf_results'):
        df_idf, params_gumbel, params_lp3, _, gumbel_params_tuple, lp3_params_tuple = st.session_state.get('idf_results')
        
        duracao_calculada = st.session_state.get('duracao_idf_calculada')

        if df_idf is None:
            st.warning("Série curta para ajuste estatístico (mínimo de 5 anos de dados).")
        else:
            st.session_state.update({
                'gumbel_params_tuple': gumbel_params_tuple, 'lp3_params_tuple': lp3_params_tuple,
                'df_idf': df_idf,
                'params_gumbel': params_gumbel, 'params_lp3': params_lp3
            })

            fig_idf = go.Figure()
            fig_idf.add_trace(go.Scatter(x=df_idf["TR (anos)"], y=df_idf[f"Gumbel_{duracao_calculada}h (mm)"], mode='lines+markers', name='Gumbel', line=dict(color='#D55E00')))
            fig_idf.add_trace(go.Scatter(x=df_idf["TR (anos)"], y=df_idf[f"LP3_{duracao_calculada}h (mm)"], mode='lines+markers', name='Log-Pearson III', line=dict(color='#0072B2')))
            fig_idf.update_layout(
                title=f"Precipitação Estimada vs. Período de Retorno (Duração: {duracao_calculada}h)",
                xaxis_title="Período de Retorno (anos)", yaxis_title="Precipitação (mm)",
                xaxis_type="log", template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            st.plotly_chart(fig_idf, use_container_width=True)

            fig_pdf = go.Figure(fig_idf)
            fig_pdf.update_layout(
                template="plotly_white", 
                paper_bgcolor='white', 
                plot_bgcolor='white',
                font=dict(color="black"),
                xaxis=dict(gridcolor="lightgrey", linecolor="black", title_font=dict(color="black"), tickfont=dict(color="black")),
                yaxis=dict(gridcolor="lightgrey", linecolor="black", title_font=dict(color="black"), tickfont=dict(color="black")),
                title_font=dict(color="black"),
                legend=dict(font=dict(color="black"))
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig_pdf.write_image(tmpfile.name, scale=2)
                st.session_state['grafico_path'] = tmpfile.name
            
            st.subheader("Resultados da Análise IDF")
            st.dataframe(df_idf.style.format("{:.2f}"))
            
            st.divider()
            st.subheader("Parâmetros do Ajuste Estatístico")
            
            st.markdown("##### **Distribuição Gumbel**")
            col1, col2, col3 = st.columns(3)
            col1.metric("Posição (μ)", f"{params_gumbel['mu']:.2f} mm")
            col2.metric("Escala (β)", f"{params_gumbel['beta']:.2f} mm")
            col3.metric("K-S (p-valor)", f"{params_gumbel['ks_p']:.3f}", 
                        delta="Boa aderência" if params_gumbel['ks_p'] > 0.05 else "Aderência fraca", 
                        delta_color="normal")
            
            st.markdown("##### **Distribuição Log-Pearson III**")
            col4, col5, col6 = st.columns(3)
            col4.metric("Média (log10)", f"{params_lp3['mean_log']:.3f}")
            col5.metric("Desvio Padrão (log10)", f"{params_lp3['std_log']:.3f}")
            col6.metric("Assimetria (log10)", f"{params_lp3['skew']:.3f}")

# --- ABA 3: CHUVA DE PROJETO ---
elif pagina_selecionada == "Chuva de Projeto":
    st.markdown("## <i class='fas fa-cloud-showers-heavy'></i> Cálculo de Chuva de Projeto", unsafe_allow_html=True)
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            tr_tab4 = st.number_input("Período de Retorno (anos):", min_value=1, step=1, value=10)
            dur_tab4 = st.number_input("Duração da Chuva (horas):", min_value=0.1, step=0.1, value=1.0)
        with col2:
            metodo_tab4 = st.radio("Método de Cálculo:", ["Gumbel", "Log-Pearson III"])

        if st.button("Calcular Chuva de Projeto"):
            gumbel_params = st.session_state.get('gumbel_params_tuple')
            lp3_params = st.session_state.get('lp3_params_tuple')

            if (metodo_tab4 == "Gumbel" and not gumbel_params) or \
               (metodo_tab4 == "Log-Pearson III" and not lp3_params):
                st.error("Parâmetros não encontrados. Por favor, calcule as Curvas IDF na página anterior primeiro.")
                st.session_state['show_project_results'] = False
            else:
                try:
                    dur_calculada = st.session_state.get('duracao_idf_calculada', 'N/A')
                    st.warning(f"Atenção: O cálculo usa os parâmetros ajustados para a duração de **{dur_calculada} horas**. A intensidade resultante é mais precisa quando a duração da chuva é próxima a este valor.")

                    chuva_proj = calcular_chuva_projeto(
                        tr=tr_tab4, metodo=metodo_tab4,
                        gumbel_params=gumbel_params, lp3_params=lp3_params
                    )
                    intensidade_proj = chuva_proj / dur_tab4 if dur_tab4 > 0 else 0
                    st.session_state['intensidade_proj_result'] = intensidade_proj
                    st.session_state['chuva_proj_result'] = chuva_proj
                    st.session_state['show_project_results'] = True
                except Exception as e:
                    st.error(f"Ocorreu um erro no cálculo: {e}")
                    st.session_state['show_project_results'] = False

    if st.session_state.get('show_project_results', False):
        st.divider()
        st.subheader("Resultados")
        col1, col2 = st.columns(2)
        col1.metric("Chuva de Projeto (mm)", f"{st.session_state.get('chuva_proj_result', 0):.2f}")
        col2.metric("Intensidade de Projeto (mm/h)", f"{st.session_state.get('intensidade_proj_result', 0):.2f}")
    else:
        st.info("Aguardando cálculo da chuva de projeto.")

# --- ABA 4: TEMPO DE CONCENTRAÇÃO ---
elif pagina_selecionada == "Tempo de Concentração":
    st.markdown("## <i class='fas fa-stopwatch'></i> Tempo de Concentração", unsafe_allow_html=True)
    metodo_tc = st.selectbox("Selecione o método de cálculo:", ["Kirpich", "Giandotti"])

    if metodo_tc == "Kirpich":
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                L_kirpich = st.number_input("Comprimento do curso d'água (m)", min_value=1.0, value=500.0)
            with c2:
                i_kirpich = st.number_input("Declividade média (m/m)", min_value=0.001, value=0.02, format="%.3f")
        if st.button("Calcular Tc (Kirpich)"):
            tc_min = calcular_tc_kirpich(L_kirpich, i_kirpich)
            st.success(f"Tempo de concentração (Kirpich): **{tc_min:.2f} minutos**")
            st.session_state["tc_min"] = tc_min
    
    elif metodo_tc == "Giandotti":
        with st.container(border=True):
            c1, c2 = st.columns(2)
            c3, c4 = st.columns(2)
            with c1:
                A_giandotti = st.number_input("Área da bacia (km²)", min_value=0.01, value=0.50)
            with c2:
                L_giandotti = st.number_input("Comprimento do percurso (km)", min_value=0.10, value=1.00)
            with c3:
                Hmax = st.number_input("Cota máxima da bacia (m)", value=120.0)
            with c4:
                Hmin = st.number_input("Cota mínima da bacia (m)", value=100.0)
        if st.button("Calcular Tc (Giandotti)"):
            deltaH = Hmax - Hmin
            if deltaH > 0:
                tc_min = calcular_tc_giandotti(A_giandotti, L_giandotti, deltaH)
                st.success(f"Tempo de concentração (Giandotti): **{tc_min:.2f} minutos**")
                st.session_state["tc_min"] = tc_min
            else:
                st.warning("A cota máxima deve ser maior que a mínima.")

# --- ABA 5: VAZÃO DE PROJETO ---
elif pagina_selecionada == "Vazão de Projeto":
    st.markdown("## <i class='fas fa-calculator'></i> Vazão de Projeto – Método Racional", unsafe_allow_html=True)
    intensidade_chuva = st.session_state.get("intensidade_proj_result")
    
    if intensidade_chuva:
        st.info(f"Intensidade de projeto recuperada: **{intensidade_chuva:.2f} mm/h**")
    else:
        st.warning("Calcule a intensidade da chuva na página 'Chuva de Projeto' primeiro.")
    
    C = st.number_input("Coeficiente de escoamento (C)", 0.1, 1.0, 0.6)
    A = st.number_input("Área de contribuição (ha)", min_value=0.01, value=5.0)
    
    if st.button("Calcular Vazão de Projeto"):
        if intensidade_chuva:
            Q = calcular_vazao_racional(C, intensidade_chuva, A)
            st.success(f"**Vazão de projeto estimada: {Q:.3f} m³/s**")
            st.session_state["q_projeto"] = Q
            st.session_state["vazao_C"] = C
            st.session_state["vazao_A"] = A
        else:
            st.error("Não foi possível calcular. A intensidade da chuva não foi definida.")

# --- ABA 6: CONDUTOS CIRCULARES ---
elif pagina_selecionada == "Condutos Circulares":
    st.markdown("## <i class='fas fa-arrows-left-right-to-line'></i> Dimensionamento de Condutos Circulares", unsafe_allow_html=True)
    
    Q_default = st.session_state.get("q_projeto", 0.0)
    Q = st.number_input("Vazão de Projeto Q (m³/s)", min_value=0.0, value=Q_default, format="%.3f")

    with st.container(border=True):
        c1, c2 = st.columns(2)
        n = c1.number_input("Coeficiente de Manning (n)", min_value=0.010, value=0.013, format="%.3f")
        S = c2.number_input("Declividade do conduto S (m/m)", min_value=0.0001, value=0.0100, format="%.4f")

    if st.button("Dimensionar Conduto"):
        if Q > 0:
            with st.spinner("Calculando..."):
                d_rec, Q_calc = dimensionar_conduto_circular(Q, n, S, d_min_m=0.05, d_max_m=3.0, passo_m=0.01)
            
            if d_rec:
                st.success(f"**Diâmetro mínimo recomendado: {d_rec:.3f} m**")
                A = (math.pi / 4.0) * d_rec**2
                R = d_rec / 4.0
                V = Q_calc / A if A > 0 else 0
                tau = tau_medio(R, S)
                
                c1, c2 = st.columns(2)
                c1.metric("Vazão de capacidade do conduto", f"{Q_calc:.3f} m³/s")
                c2.metric("Velocidade de escoamento", f"{V:.3f} m/s")
                c1.metric("Área da seção cheia", f"{A:.3f} m²")
                c2.metric("Tensão de arraste média", f"{tau:.2f} Pa")
                
                st.session_state['conduto_d_rec'] = d_rec
                st.session_state['conduto_Q_calc'] = Q_calc
                st.session_state['conduto_V'] = V
            else:
                st.error("Nenhum diâmetro no intervalo padrão atendeu à vazão de projeto.")
        else:
            st.info("A vazão de projeto deve ser maior que zero.")

# --- ABA 7: CANAIS ABERTOS ---
elif pagina_selecionada == "Canais Abertos":
    st.markdown("## <i class='fas fa-water'></i> Análise de Canais Abertos", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("Parâmetros Gerais do Canal")
        c1, c2 = st.columns(2)
        S_canal = c1.number_input("Declividade do canal (S)", value=0.001, format="%.4f", key="canal_S")
        mat = c2.selectbox("Material (rugosidade típica)", list(MATERIAIS_MANNING.keys()), index=0, key="canal_mat")
        n_canal = st.number_input("Coeficiente de Manning (n)", value=float(MATERIAIS_MANNING[mat]), format="%.3f", key="canal_n")
        
        tipo = st.selectbox("Tipo de seção", ["Trapezoidal", "Retangular", "Triangular"], key="canal_tipo")
        
        b = 0.0
        z = 0.0
        
        if tipo == "Trapezoidal":
            c3, c4 = st.columns(2)
            b = c3.number_input("Largura da base (b)", value=1.0, key="canal_b_trap")
            z = c4.number_input("Talude (z)", value=1.5, key="canal_z_trap")
        elif tipo == "Retangular":
            b = st.number_input("Largura (b)", value=1.0, key="canal_b_ret")
            z = 0.0
        elif tipo == "Triangular":
            b = 0.0
            z = st.number_input("Talude (z)", value=1.5, key="canal_z_tri")

    st.divider()
    st.subheader("Calculadoras Hidráulicas")
    
    with st.container(border=True):
        st.markdown("#### 1. Verificar Capacidade da Seção")
        y_verif = st.number_input("Profundidade (y) para verificação", value=0.5, key="y_verif")
        if st.button("Verificar Vazão"):
            A, P, T = geom_trapezio(b, z, y_verif)
            Q_calc = manning_Q(A, P, S_canal, n_canal)
            st.metric("Capacidade de vazão do canal", f"{Q_calc:.3f} m³/s")

    with st.container(border=True):
        st.markdown("#### 2. Dimensionar Profundidade (y)")
        q_dim_y = st.number_input("Vazão de Projeto (Q)", min_value=0.0, value=st.session_state.get("q_projeto", 0.0), format="%.3f", key="q_dim_y")
        if st.button("Calcular Profundidade (y)"):
            if q_dim_y > 0:
                yn = y_normal(q_dim_y, b, z, S_canal, n_canal)
                if yn:
                    st.success(f"**Profundidade normal (y) encontrada: {yn:.3f} m**")
                    yc = y_critico(q_dim_y, b, z)
                    regime = "Subcrítico" if yn > yc else "Supercrítico"
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Profundidade Crítica (yc)", f"{yc:.3f} m")
                    c2.metric("Regime de Escoamento", regime)

                    st.session_state['canal_yn'] = yn
                    st.session_state['canal_yc'] = yc
                    st.session_state['canal_regime'] = regime
                else:
                    st.error("Não foi possível encontrar a profundidade.")
            else:
                st.warning("Informe uma vazão de projeto > 0.")

    with st.container(border=True):
        st.markdown("#### 3. Dimensionar Largura da Base (b)")
        q_dim_b = st.number_input("Vazão de Projeto (Q)", min_value=0.0, value=st.session_state.get("q_projeto", 0.0), format="%.3f", key="q_dim_b")
        y_proj = st.number_input("Profundidade de projeto (y)", value=0.5, key="y_proj_b")
        if st.button("Calcular Largura (b)", disabled=(tipo=="Triangular")):
            if tipo == "Triangular":
                st.info("O dimensionamento de largura não se aplica a canais triangulares (b=0).")
            elif q_dim_b > 0:
                b_sol = b_para_Q(q_dim_b, z, y_proj, S_canal, n_canal)
                if b_sol:
                    st.success(f"**Largura (b) encontrada: {b_sol:.3f} m**")
                else:
                    st.error("Não foi possível encontrar a largura.")
            else:
                st.warning("Informe uma vazão de projeto > 0.")

# --- ABA 8: RELATÓRIO PDF ---
elif pagina_selecionada == "Relatório PDF":
    st.markdown("## <i class='fas fa-file-alt'></i> Relatório em PDF", unsafe_allow_html=True)
    
    if st.session_state.get('df_idf') is not None and st.session_state.get('grafico_path') is not None:
        st.info(f"Pronto para gerar o relatório com todos os dados calculados até o momento.")
        
        dados_para_relatorio = {
            "idf": {
                "df_idf": st.session_state.get('df_idf'),
                "fig_path": st.session_state.get('grafico_path'),
                "duracao": st.session_state.get('duracao_idf_calculada'),
                "params_gumbel": st.session_state.get('params_gumbel'),
                "params_lp3": st.session_state.get('params_lp3')
            },
            "chuva_projeto": {
                "intensidade": st.session_state.get('intensidade_proj_result'),
                "chuva_total": st.session_state.get('chuva_proj_result'),
            },
            "tc": {
                "tc_min": st.session_state.get('tc_min')
            },
            "vazao": {
                "q_projeto": st.session_state.get('q_projeto'),
                "C": st.session_state.get('vazao_C'),
                "A": st.session_state.get('vazao_A')
            },
            "conduto": {
                "diametro": st.session_state.get('conduto_d_rec'),
                "vazao_calc": st.session_state.get('conduto_Q_calc'),
                "velocidade": st.session_state.get('conduto_V'),
            },
            "canal": {
                "tipo": st.session_state.get('canal_tipo'),
                "yn": st.session_state.get('canal_yn'),
                "yc": st.session_state.get('canal_yc'),
                "regime": st.session_state.get('canal_regime'),
            }
        }

        pdf_bytes = gerar_pdf_bytes(dados_para_relatorio)
        
        st.download_button(
            label="Baixar Relatório Completo em PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_PLUVIAH.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning("Calcule uma curva IDF primeiro para poder gerar o relatório.")
