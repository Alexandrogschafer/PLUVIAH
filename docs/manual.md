# Manual do PLUVIAH

## Tempo de concentração

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
