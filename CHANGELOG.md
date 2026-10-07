# Changelog

Todas as mudanças relevantes do PLUVIAH são registradas neste arquivo.
O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [1.1.0] — em preparação

### Mudanças que alteram resultados em relação à v1.0.0

Quem tem resultados obtidos na v1.0.0 deve recalculá-los nos quatro pontos abaixo.

- **Tempo de concentração de Giandotti: fórmula corrigida.** A v1.0.0 usava uma fórmula incorreta, `Tc(h) = (4·A + 1,5·L) / (0,8·ΔH)`. A v1.1.0 usa `Tc(h) = (4·√A + 1,5·L) / (0,8·√H)`, com `H` = altitude média da bacia menos a cota do exutório. Para A = 10 km², L = 5 km e altura de 100 m, o resultado passa de 35,6 min para 151,1 min. No painel, os campos "cota máxima" e "cota mínima" foram substituídos por "altitude média da bacia" e "cota do exutório".
- **Condutos circulares: diâmetros comerciais.** O diâmetro recomendado deixa de ser calculado em passos de 1 cm e passa a ser o menor diâmetro nominal da série comercial de tubos de concreto (DN 300 a DN 2000, ABNT NBR 8890) que atende à capacidade a seção cheia e ao enchimento máximo (y/D) configurado. Para Q = 0,3 m³/s, n = 0,013 e S = 0,01, o resultado passa de 0,460 m para DN 500.
- **Condutos circulares: velocidade exibida.** A velocidade apresentada passa a ser a da vazão de projeto na seção parcialmente cheia do diâmetro adotado. Na v1.0.0 era a velocidade a seção cheia, na vazão de capacidade. No mesmo exemplo, passa de 1,82 m/s para 2,13 m/s.
- **Testes de aderência: p-valores.** Os p-valores passam a ser calculados por Monte Carlo (999 amostras, semente fixa), com os parâmetros reestimados em cada amostra simulada. O p-valor do teste K-S de Gumbel, único exibido na v1.0.0, era o tabelado, que trata os parâmetros como conhecidos e sai otimista; os valores da v1.1.0 diferem para a mesma série.

### Adicionado

- Distribuição GEV (Generalizada de Valores Extremos) no ajuste das curvas IDF, no gráfico, na chuva de projeto e no relatório PDF. O parâmetro de forma é reportado como ξ.
- Testes de aderência K-S e Anderson-Darling para as três distribuições (Gumbel, Log-Pearson III e GEV), no painel e no relatório PDF.
- Verificação da razão de enchimento (y/D) em condutos circulares, com critério de projeto configurável (padrão 0,85).
- Diâmetro mínimo de projeto configurável (padrão DN 300) e exibição do diâmetro teórico mínimo ao lado do diâmetro comercial adotado.
- Aviso explícito quando nenhum diâmetro da série atende à vazão de projeto ou ao enchimento máximo.
- Alertas de faixa de aplicabilidade para os métodos de Kirpich (área, declividade e comprimento) e Giandotti (área), conforme Silveira (2005). Os alertas não bloqueiam o cálculo. A aba de Kirpich passa a pedir a área da bacia.
- Nota na aba de Giandotti: método para bacias maiores, incluído para comparação didática.
- Manual (`docs/manual.md`): método de Giandotti e sua correção, faixas de aplicabilidade e procedimento dos testes de aderência.
- Testes automatizados para `y_normal`, `y_critico`, `b_para_Q`, `calculate_idf_curves`, `calcular_chuva_projeto`, GEV, testes de aderência, alertas de faixa e dimensionamento de condutos (de 16 para 75 testes).

### Alterado

- O cálculo das curvas IDF leva cerca de 40 segundos por duração, por causa dos testes de aderência por Monte Carlo. O resultado fica em cache para a mesma série e duração.
- A tabela IDF e o relatório PDF incluem as colunas da GEV; o cabeçalho da tabela no PDF ajusta a fonte à largura da coluna.
- `calculate_idf_curves` retorna oito valores (antes seis), com os parâmetros da GEV ao final.
- `dimensionar_conduto_circular` tem nova assinatura: recebe a série de diâmetros, o diâmetro mínimo e o critério de enchimento, e retorna o diâmetro nominal em milímetros.
- Dependência mínima: `scipy>=1.15`.

### Corrigido

- `tests/test_imports.py` falhava com `pytest` puro (`No module named 'pluviah'`); corrigido com `pytest.ini`.
- Aviso de descontinuação do SciPy no teste de Anderson-Darling.

## Planejado para a v1.2.0

- Persistência do projeto: exportar e importar os dados e resultados da sessão em arquivo JSON.

## [1.0.0] — 2026-07-04

- Primeira versão pública.
