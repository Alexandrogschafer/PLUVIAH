import pandas as pd

def load_data(uploaded_file):
    """Lê e processa o arquivo CSV de chuvas."""
    df_raw = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8')
    df_raw.columns = [col.strip().lower() for col in df_raw.columns]

    if "precipitacao" in df_raw.columns:
        df_raw["precipitacao"] = pd.to_numeric(
            df_raw["precipitacao"].astype(str).str.replace(",", "."), errors='coerce'
        )
    else:
        raise ValueError("Coluna 'precipitacao' não encontrada.")

    if "datahora" in df_raw.columns:
        df_raw["datahora"] = pd.to_datetime(df_raw["datahora"], errors='coerce')
    elif "data" in df_raw.columns and "hora" in df_raw.columns:
        df_raw["hora"] = df_raw["hora"].astype(str).str.zfill(4)
        df_raw["datahora"] = pd.to_datetime(
            df_raw["data"].astype(str) + " " + df_raw["hora"].str[:2] + ":" + df_raw["hora"].str[2:],
            format="%Y-%m-%d %H:%M",
            errors="coerce"
        )
    else:
        raise ValueError("Colunas de data e hora não reconhecidas. Use 'datahora' ou 'data' e 'hora'.")

    df_raw = df_raw.dropna(subset=["datahora", "precipitacao"])
    df = df_raw[["datahora", "precipitacao"]].sort_values("datahora").set_index("datahora")
    return df
