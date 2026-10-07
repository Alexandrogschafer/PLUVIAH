# idf.py

import pandas as pd
import numpy as np
from scipy.stats import gumbel_r, pearson3, genextreme, goodness_of_fit
from config import N_MC_ADERENCIA, SEMENTE_ADERENCIA

def _teste_aderencia(dist, dados, params_ajustados, n_mc):
    """
    Testes de aderencia K-S e Anderson-Darling por Monte Carlo (scipy.stats.goodness_of_fit).

    A estatistica dos dados e calculada contra a distribuicao ajustada (params_ajustados).
    Em cada amostra simulada os parametros sao reestimados, de modo que o p-valor leva em
    conta que eles foram estimados na propria amostra (sem isso o p-valor sai otimista).
    A semente e fixa (config.SEMENTE_ADERENCIA) para o resultado ser reprodutivel.
    """
    resultado = {}
    for estatistica in ("ks", "ad"):
        res = goodness_of_fit(
            dist, dados, fit_params=params_ajustados, guessed_params=params_ajustados,
            statistic=estatistica, n_mc_samples=n_mc, rng=SEMENTE_ADERENCIA
        )
        resultado[f"{estatistica}_stat"] = res.statistic
        resultado[f"{estatistica}_p"] = res.pvalue
    return resultado

def calculate_annual_maxima(df, duration):
    """Calcula as maximas anuais para uma dada duracao."""
    accumulated = df["precipitacao"].rolling(window=duration, min_periods=1).sum()
    annual_maxima = accumulated.groupby(df.index.year).max().dropna()
    return annual_maxima

def calculate_idf_curves(series, duration, trs_np, n_mc=N_MC_ADERENCIA):
    """
    Ajusta as distribuicoes Gumbel, Log-Pearson III e GEV e retorna os parametros.
    n_mc e o numero de amostras de Monte Carlo dos testes de aderencia.
    """
    if len(series) < 5:
        return None, None, None, series, None, None, None, None

    # --- Gumbel ---
    mu_g, beta_g = gumbel_r.fit(series.values)
    aderencia_gumbel = _teste_aderencia(gumbel_r, series.values, {"loc": mu_g, "scale": beta_g}, n_mc)
    intensities_gumbel = [gumbel_r.ppf(1 - 1/tr, loc=mu_g, scale=beta_g) for tr in trs_np]
    
    # --- Log-Pearson III ---
    # Garante que nao haja valores <= 0 para o log
    dados_log = np.log10(series.values[series.values > 0])
    skew = pd.Series(dados_log).skew()
    mean_log = np.mean(dados_log)
    std_log = np.std(dados_log, ddof=1)
    lp3_dist = pearson3(skew, loc=mean_log, scale=std_log)
    intensities_lp3 = [10 ** lp3_dist.ppf(1 - 1/tr) for tr in trs_np]

    # Aderencia em escala log10, o espaco onde a LP3 foi ajustada
    aderencia_lp3 = _teste_aderencia(
        pearson3, dados_log, {"skew": skew, "loc": mean_log, "scale": std_log}, n_mc
    )

    # --- GEV (Generalizada de Valores Extremos) ---
    # Ajuste por maxima verossimilhanca. O SciPy usa o parametro de forma c = -xi;
    # aqui se reporta xi (convencao usual em hidrologia): xi > 0 cauda pesada (Frechet),
    # xi = 0 Gumbel, xi < 0 cauda limitada (Weibull).
    c_gev, loc_gev, scale_gev = genextreme.fit(series.values)
    intensities_gev = [genextreme.ppf(1 - 1/tr, c_gev, loc=loc_gev, scale=scale_gev) for tr in trs_np]
    aderencia_gev = _teste_aderencia(
        genextreme, series.values, {"c": c_gev, "loc": loc_gev, "scale": scale_gev}, n_mc
    )

    df_idf = pd.DataFrame({
        "TR (anos)": trs_np,
        f"Gumbel_{duration}h (mm)": intensities_gumbel,
        f"LP3_{duration}h (mm)": intensities_lp3,
        f"GEV_{duration}h (mm)": intensities_gev,
        f"Intensidade_Gumbel_{duration}h (mm/h)": np.array(intensities_gumbel) / duration,
        f"Intensidade_LP3_{duration}h (mm/h)": np.array(intensities_lp3) / duration,
        f"Intensidade_GEV_{duration}h (mm/h)": np.array(intensities_gev) / duration
    })
    
    params_gumbel = {
        "mu": mu_g, "beta": beta_g, **aderencia_gumbel
    }
    params_lp3 = {
        "mean_log": mean_log, "std_log": std_log, "skew": skew, **aderencia_lp3
    }
    
    gumbel_params_tuple = (mu_g, beta_g)
    lp3_params_tuple = (mean_log, std_log, skew)

    params_gev = {
        "xi": -c_gev, "loc": loc_gev, "scale": scale_gev, **aderencia_gev
    }
    gev_params_tuple = (-c_gev, loc_gev, scale_gev)

    return (df_idf, params_gumbel, params_lp3, series, gumbel_params_tuple, lp3_params_tuple,
            params_gev, gev_params_tuple)

def calcular_chuva_projeto(tr, metodo, gumbel_params, lp3_params, gev_params=None):
    """Calcula a precipitacao de projeto a partir dos parametros ajustados."""
    if metodo == "Gumbel":
        if not gumbel_params:
            raise ValueError("Parametros Gumbel nao fornecidos.")
        mu, beta = gumbel_params
        return gumbel_r.ppf(1 - 1 / float(tr), loc=mu, scale=beta)
    
    elif metodo == "Log-Pearson III":
        if not lp3_params:
            raise ValueError("Parametros Log-Pearson III nao fornecidos.")
        mean_log, std_log, skew = lp3_params
        dist_lp3 = pearson3(skew, loc=mean_log, scale=std_log)
        return 10 ** dist_lp3.ppf(1 - 1 / float(tr))
    
    elif metodo == "GEV":
        if not gev_params:
            raise ValueError("Parametros GEV nao fornecidos.")
        xi, loc, scale = gev_params
        return genextreme.ppf(1 - 1 / float(tr), -xi, loc=loc, scale=scale)

    raise ValueError(f"Metodo de calculo '{metodo}' invalido.")
