# relatorio.py

from fpdf import FPDF
import streamlit as st

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Análise Pluviométrica e Hidráulica - PLUVIAH', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, content):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, content)
        self.ln()

    def create_table(self, df, title):
        self.set_font("Arial", 'B', 12)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", '', 10)
        
        col_widths = [25] + [165 // (len(df.columns) -1)] * (len(df.columns)-1)
        headers = df.columns
        
        self.set_fill_color(220, 220, 220)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, str(header), 1, 0, 'C', 1)
        self.ln()

        for _, row in df.iterrows():
            for i, item in enumerate(row):
                text = f"{item:.2f}" if isinstance(item, float) else str(item)
                self.cell(col_widths[i], 8, text, 1, 0, 'C')
            self.ln()
        self.ln(10)


def _construir_pdf(dados_relatorio):
    pdf = PDF()
    pdf.add_page()
    
    # --- Seção 1: Curvas IDF ---
    if 'idf' in dados_relatorio:
        dados_idf = dados_relatorio['idf']
        pdf.chapter_title(f"1. Curvas IDF (Duração: {dados_idf['duracao']} horas)")
        
        if dados_idf.get('fig_path'):
            pdf.image(dados_idf['fig_path'], x=10, y=None, w=190)
            pdf.ln(5)
            
        if dados_idf.get('df_idf') is not None:
            pdf.create_table(dados_idf['df_idf'], "Tabela de Precipitações e Intensidades")

        if dados_idf.get('params_gumbel'):
            params = dados_idf['params_gumbel']
            texto_gumbel = (
                f"Distribuição Gumbel:\n"
                f"  - Parâmetro de Posição (mu): {params.get('mu', 0):.2f} mm\n"
                f"  - Parâmetro de Escala (beta): {params.get('beta', 0):.2f} mm\n"
                f"  - Teste K-S (p-valor): {params.get('ks_p', 0):.4f} "
                f"({'Aceito' if params.get('ks_p', 0) > 0.05 else 'Rejeitado'} a 5% de significância)"
            )
            pdf.chapter_body(texto_gumbel)

        if dados_idf.get('params_lp3'):
            params = dados_idf['params_lp3']
            texto_lp3 = (
                f"Distribuição Log-Pearson III:\n"
                f"  - Média (log10): {params.get('mean_log', 0):.3f}\n"
                f"  - Desvio Padrão (log10): {params.get('std_log', 0):.3f}\n"
                f"  - Coef. de Assimetria (log10): {params.get('skew', 0):.3f}"
            )
            pdf.chapter_body(texto_lp3)
    
    pdf.add_page()
    
    # --- Seção 2: Parâmetros de Projeto ---
    pdf.chapter_title("2. Parâmetros de Projeto")
    texto_params = ""
    if 'chuva_projeto' in dados_relatorio and dados_relatorio['chuva_projeto'].get('intensidade') is not None:
        dados = dados_relatorio['chuva_projeto']
        texto_params += (
            f"Chuva de Projeto:\n"
            f"  - Intensidade (i): {dados['intensidade']:.2f} mm/h\n"
            f"  - Chuva Total (P): {dados['chuva_total']:.2f} mm\n\n"
        )
    if 'tc' in dados_relatorio and dados_relatorio['tc'].get('tc_min') is not None:
        dados = dados_relatorio['tc']
        texto_params += f"Tempo de Concentração (Tc): {dados['tc_min']:.2f} minutos\n\n"
    if 'vazao' in dados_relatorio and dados_relatorio['vazao'].get('q_projeto') is not None:
        dados = dados_relatorio['vazao']
        texto_params += (
            f"Vazão de Projeto (Método Racional):\n"
            f"  - Coeficiente (C): {dados.get('C', 0):.2f}\n"
            f"  - Área (A): {dados.get('A', 0):.2f} ha\n"
            f"  - Vazão de Projeto (Q): {dados['q_projeto']:.3f} m³/s\n"
        )
    pdf.chapter_body(texto_params or "Nenhum parâmetro de projeto foi calculado.")

    # --- Seção 3: Dimensionamento Hidráulico ---
    pdf.chapter_title("3. Dimensionamento Hidráulico")
    texto_hidraulico = ""
    
    # --- ALTERAÇÃO AQUI: Verifica se o valor principal (diametro) existe ---
    if 'conduto' in dados_relatorio and dados_relatorio['conduto'].get('diametro') is not None:
        dados = dados_relatorio['conduto']
        texto_hidraulico += (
            f"Conduto Circular:\n"
            f"  - Diâmetro Recomendado: {dados['diametro']:.3f} m\n"
            f"  - Vazão de Capacidade: {dados['vazao_calc']:.3f} m³/s\n"
            f"  - Velocidade: {dados['velocidade']:.3f} m/s\n\n"
        )
        
    # --- ALTERAÇÃO AQUI: Verifica se o valor principal (yn) existe ---
    if 'canal' in dados_relatorio and dados_relatorio['canal'].get('yn') is not None:
        dados = dados_relatorio['canal']
        texto_hidraulico += (
            f"Canal Aberto ({dados.get('tipo', 'N/A')}):\n"
            f"  - Profundidade Normal (yn): {dados['yn']:.3f} m\n"
            f"  - Profundidade Crítica (yc): {dados['yc']:.3f} m\n"
            f"  - Regime: {dados.get('regime', 'N/A')}\n"
        )
    
    pdf.chapter_body(texto_hidraulico or "Nenhum dimensionamento hidráulico foi realizado.")

    return pdf

@st.cache_data
def gerar_pdf_bytes(dados_relatorio):
    pdf = _construir_pdf(dados_relatorio)
    return bytes(pdf.output(dest='S'))
