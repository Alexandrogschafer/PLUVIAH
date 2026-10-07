# idf.py

import pandas as pd
import numpy as np
from scipy.stats import gumbel_r, pearson3, genextreme, kstest, anderson, goodness_of_fit

def _anderson_darling_gumbel(z):
    """Teste Anderson-Darling para Gumbel sobre dados padronizados. Retorna (estatistica, p-valor).
    O p-valor e interpolado da tabela de valores criticos, portanto limitado a [0.01, 0.25]."""
    try:
        # SciPy >= 1.17: `method` e obrigatorio a partir do 1.19
        res = anderson(z, dist='gumbel_r', method='interpolate')
        return res.statistic, res.pvalue
    except TypeError:
        # SciPy < 1.17: sem o parametro `method`; interpola na tabela de valores criticos
        res = anderson(z, dist='gumbel_r')
        p = np.interp(res.statistic, res.critical_values, res.significance_level / 100.0)
        return res.statistic, p

def calculate_annual_maxima(df, duration):
    """Calcula as maximas anuais para uma dada duracao."""
    accumulated = df["precipitacao"].rolling(window=duration, min_periods=1).sum()
    annual_maxima = accumulated.groupby(df.index.year).max().dropna()
    return annual_maxima

def calculate_idf_curves(series, duration, trs_np):
    """Ajusta as distribuicoes Gumbel, Log-Pearson III e GEV e retorna os parametros."""
    if len(series) < 5:
        return None, None, None, series, None, None, None, None

    # --- Gumbel ---
    mu_g, beta_g = gumbel_r.fit(series.values)
    _, ks_p = kstest(series.values, 'gumbel_r', args=(mu_g, beta_g))
    # Teste Anderson-Darling é mais sensível nas caudas da distribuição
    ad_stat, ad_p = _anderson_darling_gumbel((series.values - mu_g) / beta_g)
    intensities_gumbel = [gumbel_r.ppf(1 - 1/tr, loc=mu_g, scale=beta_g) for tr in trs_np]
    
    # --- Log-Pearson III ---
    # Garante que nao haja valores <= 0 para o log
    dados_log = np.log10(series.values[series.values > 0])
    skew = pd.Series(dados_log).skew()
    mean_log = np.mean(dados_log)
    std_log = np.std(dados_log, ddof=1)
    lp3_dist = pearson3(skew, loc=mean_log, scale=std_log)
    intensities_lp3 = [10 ** lp3_dist.ppf(1 - 1/tr) for tr in trs_np]

    # Teste K-S: compara os dados em escala log10 (espaco onde a LP3 foi ajustada) com a distribuicao ajustada
    _, ks_p_lp3 = kstest(dados_log, 'pearson3', args=(skew, mean_log, std_log))
    # anderson() nao suporta 'pearson3' nativamente; goodness_of_fit calcula a estatistica AD
    # e seu p-valor via simulacao de Monte Carlo (rng fixo para resultado reprodutivel)
    ad_result_lp3 = goodness_of_fit(
        pearson3, dados_log,
        known_params={"skew": skew, "loc": mean_log, "scale": std_log},
        statistic='ad', rng=42
    )

    # --- GEV (Generalizada de Valores Extremos) ---
    # Ajuste por maxima verossimilhanca. O SciPy usa o parametro de forma c = -xi;
    # aqui se reporta xi (convencao usual em hidrologia): xi > 0 cauda pesada (Frechet),
    # xi = 0 Gumbel, xi < 0 cauda limitada (Weibull).
    c_gev, loc_gev, scale_gev = genextreme.fit(series.values)
    intensities_gev = [genextreme.ppf(1 - 1/tr, c_gev, loc=loc_gev, scale=scale_gev) for tr in trs_np]
    _, ks_p_gev = kstest(series.values, 'genextreme', args=(c_gev, loc_gev, scale_gev))
    ad_result_gev = goodness_of_fit(
        genextreme, series.values,
        known_params={"c": c_gev, "loc": loc_gev, "scale": scale_gev},
        statistic='ad', rng=42
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
        "mu": mu_g, "beta": beta_g, "ks_p": ks_p,
        "ad_stat": ad_stat, "ad_p": ad_p
    }
    params_lp3 = {
        "mean_log": mean_log, "std_log": std_log, "skew": skew,
        "ks_p": ks_p_lp3, "ad_stat": ad_result_lp3.statistic, "ad_p": ad_result_lp3.pvalue
    }
    
    gumbel_params_tuple = (mu_g, beta_g)
    lp3_params_tuple = (mean_log, std_log, skew)

    params_gev = {
        "xi": -c_gev, "loc": loc_gev, "scale": scale_gev,
        "ks_p": ks_p_gev, "ad_stat": ad_result_gev.statistic, "ad_p": ad_result_gev.pvalue
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
