# PLUVIAH

Plataforma de Análise Pluviométrica e Hidráulica

O **PLUVIAH** é um software acadêmico-institucional desenvolvido em Python (Streamlit) para apoiar engenheiros, professores e estudantes no estudo de hidrologia e hidráulica.

Ele integra, em um único ambiente:

* Processamento de séries de precipitação horária
* Ajuste de curvas IDF (Intensidade–Duração–Frequência)
* Estimativa de chuvas de projeto
* Cálculo de tempo de concentração (Kirpich e Giandotti)
* Determinação da vazão de projeto (Método Racional)
* Dimensionamento de condutos circulares e canais abertos (Manning)
* Geração de relatório consolidado em HTML/PDF

---

## Aplicações

Ensino e pesquisa
Ideal para disciplinas de Hidrologia/Hidráulica, permitindo demonstrar todo o fluxo — do dado bruto de chuva até o dimensionamento de condutos ou canais.

Estudos preliminares / dimensionamento pontual
Permite verificar rapidamente a seção de um trecho (tubo, galeria, canal trapezoidal em ponto crítico).

Relatórios técnicos simplificados
Gera relatórios consolidados de forma automática, úteis em TCCs, dissertações e pareceres técnicos iniciais.

Padronização de cálculos
Reduz erros em planilhas e cálculos manuais, garantindo clareza e reprodutibilidade.

### Limitações

* O PLUVIAH calcula seções pontuais de condutos e canais.
* Não realiza o dimensionamento automático de uma rede completa de drenagem.
* É mais indicado para fins didáticos, acadêmicos e análises preliminares.

---

## Instalação e Uso

1. Clone o repositório:

   ```bash
   git clone https://github.com/Alexandrogschafer/PLUVIAH.git
   cd PLUVIAH
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Execute o dashboard:

   ```bash
   streamlit run pluviah/dashboard.py
   ```

---

## Estrutura do Repositório

```
pluviah/         # Código-fonte principal
docs/            # Documentação, manuais e imagens
requirements.txt # Dependências do projeto
README.md        # Apresentação do projeto
LICENSE          # Licença MIT
```

---

## Licença

Este projeto está licenciado sob a MIT License.


