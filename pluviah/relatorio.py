# relatorio.py

from fpdf import FPDF
import streamlit as st

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Análise de Chuvas Intensas - Curvas IDF', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def _construir_pdf(df_idf, fig_path, duration, params_gumbel, params_lp3):
    """Função interna para construir o objeto PDF."""
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Curvas IDF para Duração de {duration} horas", ln=True, align='C')
    pdf.ln(10)

    pdf.image(fig_path, x=10, y=None, w=190)
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Tabela de Precipitações e Intensidades", ln=True)
    pdf.set_font("Arial", '', 10)
    
    pdf.set_fill_color(220, 220, 220)
    col_widths = [25, 40, 40, 45, 40]
    headers = ["TR (anos)", "Gumbel (mm)", "LP3 (mm)", "Int. Gumbel (mm/h)", "Int. LP3 (mm/h)"]
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
    pdf.ln()

    for _, row in df_idf.iterrows():
        pdf.cell(col_widths[0], 8, f"{row.iloc[0]}", 1, 0, 'C')
        pdf.cell(col_widths[1], 8, f"{row.iloc[1]:.2f}", 1, 0, 'C')
        pdf.cell(col_widths[2], 8, f"{row.iloc[2]:.2f}", 1, 0, 'C')
        pdf.cell(col_widths[3], 8, f"{row.iloc[3]:.2f}", 1, 0, 'C')
        pdf.cell(col_widths[4], 8, f"{row.iloc[4]:.2f}", 1, 1, 'C')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Parâmetros Estatísticos e Testes de Aderência", ln=True)
    pdf.set_font("Arial", '', 10)
    
    pdf.multi_cell(0, 6, 
        f"Distribuição Gumbel:\n"
        f"  - Parâmetro de Posição (mu): {params_gumbel['mu']:.2f} mm\n"
        f"  - Parâmetro de Escala (beta): {params_gumbel['beta']:.2f} mm\n"
        f"  - Teste K-S (p-valor): {params_gumbel['ks_p']:.4f} "
        f"({'Aceito' if params_gumbel['ks_p'] > 0.05 else 'Rejeitado'} a 5% de significância)\n"
    )
    pdf.multi_cell(0, 6,
        f"Distribuição Log-Pearson III:\n"
        f"  - Média (log10): {params_lp3['mean_log']:.3f}\n"
        f"  - Desvio Padrão (log10): {params_lp3['std_log']:.3f}\n"
        f"  - Coef. de Assimetria (log10): {params_lp3['skew']:.3f}"
    )
    return pdf

@st.cache_data
def gerar_pdf_bytes(df_idf, fig_path, duration, params_gumbel, params_lp3):
    """
    Gera o PDF em memória e retorna os bytes, aproveitando o cache do Streamlit.
    """
    pdf = _construir_pdf(df_idf, fig_path, duration, params_gumbel, params_lp3)
    # CORREÇÃO: Converte o 'bytearray' para o formato 'bytes' que o Streamlit espera.
    return bytes(pdf.output(dest='S'))
