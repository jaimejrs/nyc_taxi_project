import pandas as pd
import numpy as np

def aggregate_by_day(df):
    """
    Agrega métricas por dia da viagem.
    Métricas: total de corridas, receita total, ticket médio e gorjeta média.
    """
    print("Gerando agregação diária...")
    
    # Criar percentual de gorjeta para a média
    df['tip_pct'] = (df['tip_amount'] / df['total_amount'].replace(0, np.nan)).fillna(0)
    
    daily_agg = df.groupby('pickup_date_str').agg(
        total_trips=('VendorID', 'count'),
        total_revenue=('total_amount', 'sum'),
        avg_fare=('fare_amount', 'mean'),
        avg_tip_pct=('tip_pct', 'mean'),
        avg_distance=('trip_distance', 'mean'),
        avg_duration=('trip_duration_min', 'mean')
    ).reset_index()
    
    return daily_agg

def aggregate_by_shift_payment(df):
    """
    Agrega por turno do dia e tipo de pagamento.
    """
    print("Gerando agregação por turno e pagamento...")
    shift_pay_agg = df.groupby(['time_of_day', 'payment_type'], observed=True).agg(
        total_trips=('VendorID', 'count'),
        total_revenue=('total_amount', 'sum')
    ).reset_index()
    
    # Adicionar o percentual de viagens (pct_trips) dentro da agregação
    total_trips_all = shift_pay_agg['total_trips'].sum()
    shift_pay_agg['pct_trips'] = (shift_pay_agg['total_trips'] / total_trips_all) * 100
    
    return shift_pay_agg

def calculate_percentiles(df):
    """
    Calcula os percentis P50, P90 e P95 para duração, distância e tarifa.
    """
    print("Calculando percentis de distribuição...")
    
    metrics = ['trip_duration_min', 'trip_distance', 'fare_amount']
    percentiles = [0.50, 0.90, 0.95]
    
    # Usando o método quantile do Pandas
    perc_df = df[metrics].quantile(percentiles).reset_index()
    perc_df.rename(columns={'index': 'percentile'}, inplace=True)
    
    # Renomear os índices para P50, P90, P95
    perc_df['percentile'] = perc_df['percentile'].map({0.50: 'P50', 0.90: 'P90', 0.95: 'P95'})
    
    return perc_df

def aggregate_routes(df):
    """
    Lista rotas com mais volume e receita aproximando lat/lon para criar 'Zonas'.
    """
    print("Gerando agregação de rotas (origem-destino)...")
    
    # Arredondando para 2 casas decimais
    df['route_origin'] = df['pickup_latitude'].round(2).astype(str) + "," + df['pickup_longitude'].round(2).astype(str)
    df['route_dest'] = df['dropoff_latitude'].round(2).astype(str) + "," + df['dropoff_longitude'].round(2).astype(str)
    
    df['route'] = df['route_origin'] + " -> " + df['route_dest']
    
    routes_agg = df.groupby('route').agg(
        total_trips=('VendorID', 'count'),
        total_revenue=('total_amount', 'sum')
    ).sort_values(by='total_trips', ascending=False).reset_index()
    
    return routes_agg.head(10) # Retorna apenas o Top 10 rotas

if __name__ == "__main__":
    # Testando o fluxo completo com a  amostra
    from extract import load_data
    from validate import validate_data
    from transform import transform_data
    
    df_raw = load_data("data/raw/yellow_tripdata_2015-01.csv")
    if df_raw is not None:
        df_clean, score = validate_data(df_raw.head(100000), "2015-01")
        df_transformed = transform_data(df_clean)
        
        # 1. Agregação Diária
        df_daily = aggregate_by_day(df_transformed)
        print("\n--- Agregação Diária (Head) ---")
        print(df_daily.head())
        
        # 2. Agregação por Turno e Pagamento
        df_shift = aggregate_by_shift_payment(df_transformed)
        print("\n--- Agregação Turno + Pagamento (Head) ---")
        print(df_shift.head())
        
        # 3. Percentis
        df_perc = calculate_percentiles(df_transformed)
        print("\n--- Percentis ---")
        print(df_perc)