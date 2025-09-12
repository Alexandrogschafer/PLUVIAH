# idf.py

import pandas as pd
import numpy as np
from scipy.stats import gumbel_r, pearson3, kstest, anderson

def calculate_annual_maxima(df, duration):
    """Calcula as máximas anuais para uma dada duração."""
    accumulated = df["precipitacao"].rolling(window=duration, min_periods=1).sum()
    annual_maxima = accumulated.groupby(df.index.year).max().dropna()
    return annual_maxima

def calculate_idf_curves(series, duration, trs_np):
    """Ajusta as distribuições Gumbel e Log-Pearson III e retorna os parâmetros."""
    if len(series) < 5:
        return None, None, None, series, None, None

    # --- Gumbel ---
    mu_g, beta_g = gumbel_r.fit(series.values)
    _, ks_p = kstest(series.values, 'gumbel_r', args=(mu_g, beta_g))
    # Teste Anderson-Darling é mais sensível nas caudas da distribuição
    ad_result = anderson((series.values - mu_g) / beta_g, dist='gumbel_r')
    intensities_gumbel = [gumbel_r.ppf(1 - 1/tr, loc=mu_g, scale=beta_g) for tr in trs_np]
    
    # --- Log-Pearson III ---
    # Garante que não haja valores <= 0 para o log
    dados_log = np.log10(series.values[series.values > 0])
    skew = pd.Series(dados_log).skew()
    mean_log = np.mean(dados_log)
    std_log = np.std(dados_log, ddof=1)
    lp3_dist = pearson3(skew, loc=mean_log, scale=std_log)
    intensities_lp3 = [10 ** lp3_dist.ppf(1 - 1/tr) for tr in trs_np]

    df_idf = pd.DataFrame({
        "TR (anos)": trs_np,
        f"Gumbel_{duration}h (mm)": intensities_gumbel,
        f"LP3_{duration}h (mm)": intensities_lp3,
        f"Intensidade_Gumbel_{duration}h (mm/h)": np.array(intensities_gumbel) / duration,
        f"Intensidade_LP3_{duration}h (mm/h)": np.array(intensities_lp3) / duration
    })
    
    params_gumbel = {
        "mu": mu_g, "beta": beta_g, "ks_p": ks_p, 
        "ad_stat": ad_result.statistic, "ad_crit": ad_result.critical_values
    }
    params_lp3 = {"mean_log": mean_log, "std_log": std_log, "skew": skew}
    
    gumbel_params_tuple = (mu_g, beta_g)
    lp3_params_tuple = (mean_log, std_log, skew)

    return df_idf, params_gumbel, params_lp3, series, gumbel_params_tuple, lp3_params_tuple

def calcular_chuva_projeto(tr, metodo, gumbel_params, lp3_params):
    """Calcula a precipitação de projeto a partir dos parâmetros ajustados."""
    if metodo == "Gumbel":
        if not gumbel_params:
            raise ValueError("Parâmetros Gumbel não fornecidos.")
        mu, beta = gumbel_params
        return gumbel_r.ppf(1 - 1 / float(tr), loc=mu, scale=beta)
    
    elif metodo == "Log-Pearson III":
        if not lp3_params:
            raise ValueError("Parâmetros Log-Pearson III não fornecidos.")
        mean_log, std_log, skew = lp3_params
        dist_lp3 = pearson3(skew, loc=mean_log, scale=std_log)
        return 10 ** dist_lp3.ppf(1 - 1 / float(tr))
    
    raise ValueError(f"Método de cálculo '{metodo}' inválido.")
