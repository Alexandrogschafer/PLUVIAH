# Manual do PLUVIAH

## Tempo de concentração

### Método de Giandotti: variante implementada

O PLUVIAH calcula o tempo de concentração de Giandotti por uma **variante simplificada** da fórmula, e não pela forma clássica. As duas dão resultados diferentes, por isso o usuário deve saber qual está usando.

**Variante implementada** (`calcular_tc_giandotti`, em `pluviah/tc.py`):

```
tc (h) = (4·A + 1,5·L) / (0,8·ΔH)
```

**Forma clássica** encontrada na literatura:

```
tc (h) = (4·√A + 1,5·L) / (0,8·√Hm)
```

| Símbolo | Significado | Unidade |
|---|---|---|
| `A` | área da bacia | km² |
| `L` | comprimento do percurso (talvegue principal) | km |
| `ΔH` | desnível total da bacia: cota máxima menos cota mínima | m |
| `Hm` | altura média da bacia acima da seção de controle | m |

O painel devolve o resultado em minutos (`tc (h) × 60`).

### Diferenças em relação à forma clássica

1. A área entra **sem raiz quadrada** (`4·A` em vez de `4·√A`).
2. O denominador usa o desnível **sem raiz quadrada** (`0,8·ΔH` em vez de `0,8·√Hm`).
3. O desnível usado é o **desnível total** (cota máxima − cota mínima), informado no painel pelas duas cotas, e não a altura média acima do exutório.

Com isso a variante não é uma reescrita da forma clássica: os valores diferem, e a diferença muda com o tamanho e o relevo da bacia.

### Comparação numérica

Para a comparação, a forma clássica foi calculada com `Hm = ΔH`.

| A (km²) | L (km) | ΔH (m) | Variante implementada (min) | Forma clássica (min) |
|---|---|---|---|---|
| 0,5 | 1 | 50 | 5,2 | 45,9 |
| 10 | 5 | 100 | 35,6 | 151,1 |
| 200 | 30 | 300 | 211,2 | 439,8 |

Nos três casos a variante implementada resulta em tempo de concentração **menor** que o da forma clássica. Um tempo de concentração menor leva a uma intensidade de chuva maior e, pelo Método Racional, a uma vazão de projeto maior.

### Recomendação de uso

- Ao reportar um resultado obtido no PLUVIAH, identifique o método como "Giandotti (variante do PLUVIAH)" e cite a expressão acima.
- Para comparar com valores de outras fontes ou programas, confira qual forma da fórmula foi usada.
- O valor de referência coberto pelos testes automatizados é A = 10 km², L = 5 km, ΔH = 100 m, que resulta em 35,625 min (`pluviah/tests/test_tc.py`).
