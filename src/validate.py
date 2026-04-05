import pandas as pd
import numpy as np

def validate_data(df, year_month):
    """
    Aplica regras de validação e qualidade de dados.
    year_month: string no formato 'YYYY-MM' para validar integridade temporal.
    """
    print(f"Iniciando validação para o lote {year_month}...")
    
    # 1. Conversão para datetime 
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    # 2. Verificação de nulos
    null_mask = df.isnull().any(axis=1)

    # 3. Regras de anomalia e faixas plausíveis
    # Limites NYC: Lat (~40.5 a 40.9), Long (~-74.25 a -73.7)
    coord_mask = (
        (df['pickup_latitude'] < 40.5) | (df['pickup_latitude'] > 40.9) |
        (df['pickup_longitude'] < -74.25) | (df['pickup_longitude'] > -73.7) |
        (df['dropoff_latitude'] < 40.5) | (df['dropoff_latitude'] > 40.9) |
        (df['dropoff_longitude'] < -74.25) | (df['dropoff_longitude'] > -73.7)
    )

    range_mask = (
        (df['trip_distance'] <= 0) | (df['trip_distance'] > 100) |
        (df['passenger_count'] <= 0) | (df['passenger_count'] > 6) |
        (df['fare_amount'] <= 0) | (df['fare_amount'] > 500)
    )

    # 4. Consistência financeira 
    # total_amount deve ser a soma de tarifa + taxas + gorjeta (margem de erro de 0.1)
    financial_mask = (
        np.abs(df['total_amount'] - (df['fare_amount'] + df['extra'] + df['mta_tax'] + 
               df['tip_amount'] + df['tolls_amount'] + df['improvement_surcharge'])) > 0.1
    )

    # 5. Integridade temporal 
    # Fora do mês ou dropoff antes do pickup
    temporal_mask = (
        (df['tpep_pickup_datetime'].dt.strftime('%Y-%m') != year_month) |
        (df['tpep_dropoff_datetime'] <= df['tpep_pickup_datetime'])
    )

    # 6. Domínio de categorias 
    # Payment_type: 1=Credit, 2=Cash, 3=No Charge, 4=Dispute, 5=Unknown, 6=Void
    category_mask = ~df['payment_type'].isin([1, 2, 3, 4, 5, 6])

    # 7. Validação de duplicados 
    duplicate_mask = df.duplicated(subset=['tpep_pickup_datetime', 'VendorID', 'trip_distance', 'total_amount'], keep=False)

    # Criação da máscara única de invalidez com operador OU 
    invalid_mask = null_mask | coord_mask | range_mask | financial_mask | temporal_mask | category_mask | duplicate_mask

    # 8. Cálculo de Score de Qualidade (0 a 100) 
    total_rows = len(df)
    invalid_rows = invalid_mask.sum()
    quality_score = ((total_rows - invalid_rows) / total_rows) * 100

    print(f"Lote {year_month}: Quality Score = {quality_score:.2f}")
    print(f"Registros removidos: {invalid_rows}")
 
    return df[~invalid_mask].copy(), quality_score

if __name__ == "__main__":
    # Teste com amostra
    from extract import load_data
    test_path = "/mnt/dados/projetos/nyc_taxi_project/data/raw/yellow_tripdata_2015-01.csv"
    df_raw = load_data(test_path)
    if df_raw is not None:
        df_clean, score = validate_data(df_raw, "2015-01")
        print(f"Shape final: {df_clean.shape}")