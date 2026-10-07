# Manual do PLUVIAH

## Tempo de concentração

### Faixas de aplicabilidade

Os métodos de tempo de concentração são empíricos e valem para o tipo de bacia em que foram ajustados. O PLUVIAH compara os dados informados com as faixas abaixo e exibe um alerta quando algum deles está fora. O alerta **não bloqueia o cálculo**: o resultado é apresentado e cabe ao usuário avaliá-lo.

| Método | Grandeza | Faixa |
|---|---|---|
| Kirpich (1940) | área da bacia | 0,005 a 0,45 km² |
| Kirpich (1940) | declividade | 0,02 a 0,09 m/m |
| Kirpich (1940) | comprimento do curso d'água | 0,10 a 1,19 km |
| Giandotti (1934) | área da bacia | 170 a 70.000 km² |

Fonte: Kirpich (1940) e Giandotti (1934), conforme Silveira (2005), RBRH v.10, p.75-89. Os limites ficam em `pluviah/config.py`.

A área da bacia não entra na fórmula de Kirpich; a aba a solicita apenas para essa verificação.

O método de Giandotti foi desenvolvido para bacias maiores e está fora do escopo de microdrenagem. Ele permanece no PLUVIAH para comparação didática, e a aba informa isso.

### Método de Giandotti

O PLUVIAH calcula o tempo de concentração de Giandotti (1934) pela expressão:

```
Tc (h) = (4·√A + 1,5·L) / (0,8·√H)
```

| Símbolo | Significado | Unidade |
|---|---|---|
| `A` | área da bacia | km² |
| `L` | comprimento do talvegue principal | km |
| `H` | altitude média da bacia menos a cota do exutório | m |

No painel, `H` é obtido de dois campos: **altitude média da bacia** e **cota do exutório**. O cálculo só é feito se `H > 0`. O resultado é apresentado em minutos (`Tc (h) × 60`).

Exemplo: A = 10 km², L = 5 km, H = 100 m.

```
Tc = (4·√10 + 1,5·5) / (0,8·√100) = (12,649 + 7,5) / 8 = 2,519 h = 151,1 min
```

### Correção em relação à v1.0.0

A v1.0.0 calculava o método de Giandotti com uma **fórmula incorreta**, corrigida na v1.1.0:

```
v1.0.0 (incorreta):  Tc (h) = (4·A + 1,5·L) / (0,8·ΔH)
v1.1.0 (corrigida):  Tc (h) = (4·√A + 1,5·L) / (0,8·√H)
```

Os erros da v1.0.0 eram três:

1. a área entrava sem a raiz quadrada (`4·A` em vez de `4·√A`);
2. a altura entrava sem a raiz quadrada (`0,8·ΔH` em vez de `0,8·√H`);
3. a altura usada era o desnível total da bacia (cota máxima menos cota mínima), e não a altitude média menos a cota do exutório.

**Os resultados mudam.** Tempos de concentração de Giandotti obtidos na v1.0.0 devem ser recalculados. Comparação com a mesma altura nas duas expressões:

| A (km²) | L (km) | Altura (m) | v1.0.0, incorreta (min) | v1.1.0, corrigida (min) |
|---|---|---|---|---|
| 0,5 | 1 | 50 | 5,2 | 45,9 |
| 10 | 5 | 100 | 35,6 | 151,1 |
| 200 | 30 | 300 | 211,2 | 439,8 |

Nesses casos a v1.0.0 subestimava o tempo de concentração. Como um tempo de concentração menor leva a uma intensidade de chuva maior, a vazão de projeto pelo Método Racional ficava superestimada.

A comparação acima isola o efeito da expressão. Na prática a diferença depende também do dado de entrada, porque o campo de altura mudou de significado (item 3).
