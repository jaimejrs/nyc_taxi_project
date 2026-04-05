import pandas as pd
import numpy as np

def transform_data(df):
    """
    Aplica transformações de negócio e cria novas colunas.
    """
    print("Iniciando transformações e criação de features...")
    df = df.copy()

    # 1. Padronização temporal e cálculo de duração
    df['pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])
    
    # Duração da corrida em minutos
    df['trip_duration_min'] = (df['dropoff_datetime'] - df['pickup_datetime']).dt.total_seconds() / 60.0

    # 2. Faixas de distância (curta: <= 2, média: > 2 e <= 10, longa: > 10)
    df['distance_range'] = pd.cut(
        df['trip_distance'], 
        bins=[-np.inf, 2, 10, np.inf], 
        labels=['curta', 'média', 'longa']
    )

    # 3. Faixas de duração (muito curta: <= 5, normal: > 5 e <= 60, longa: > 60)
    df['duration_range'] = pd.cut(
        df['trip_duration_min'],
        bins=[-np.inf, 5, 60, np.inf],
        labels=['muito curta', 'normal', 'longa']
    )

    # 4. Turnos do dia (madrugada: 0-5, manhã: 6-11, tarde: 12-17, noite: 18-23)
    df['time_of_day'] = pd.cut(
        df['pickup_datetime'].dt.hour,
        bins=[-1, 5, 11, 17, 23],
        labels=['madrugada', 'manhã', 'tarde', 'noite']
    )

    # 5. Tratamento de divisão por zero e Rentabilidade
    # Receita por minuto
    df['revenue_per_min'] = df['total_amount'] / df['trip_duration_min']
    df['revenue_per_min'] = df['revenue_per_min'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Receita por milha
    df['revenue_per_mile'] = df['total_amount'] / df['trip_distance']
    df['revenue_per_mile'] = df['revenue_per_mile'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # 6. Flag de anomalia combinada (ex: Velocidade > 80mph e Tarifa < 5)
    speed_mph = df['trip_distance'] / (df['trip_duration_min'] / 60.0).replace(0, 0.0001)
    df['anomaly_flag'] = np.where((speed_mph > 80) & (df['fare_amount'] < 5), True, False)

    # 7. Enriquecimento de Calendário
    # Dia da semana (0=Segunda, 6=Domingo) -> Fim de semana >= 5
    df['is_weekend'] = df['pickup_datetime'].dt.dayofweek >= 5
    
    # Feriados básicos para exemplo (Ano Novo, MLK Day de 2015 e 2016)
    holidays_list = ['2015-01-01', '2015-01-19', '2016-01-01', '2016-01-18']
    df['is_holiday'] = df['pickup_datetime'].dt.strftime('%Y-%m-%d').isin(holidays_list)

    # 8. Conversão para o Parquet
    # Conversão da coluna date para texto
    df['pickup_date_str'] = df['pickup_datetime'].dt.strftime('%Y-%m-%d')
    
    # Remoção das colunas originais de timestamp textual e campos redundantes no load final
    cols_to_drop = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    print("Transformações concluídas com sucesso!")
    return df

if __name__ == "__main__":
    # Importando os scripts anteriores para testar o fluxo: Extract -> Validate -> Transform
    from extract import load_data
    from validate import validate_data
    
    test_path = "data/raw/yellow_tripdata_2015-01.csv"
    df_raw = load_data(test_path)
    
    if df_raw is not None:
        # Pega uma amostra de 100 mil linhas para testar rápido sem travar a memória
        df_sample = df_raw.head(100000)
        df_clean, score = validate_data(df_sample, "2015-01")
        df_transformed = transform_data(df_clean)
        
        print("\n--- Amostra das novas colunas ---")
        print(df_transformed[['trip_duration_min', 'distance_range', 'time_of_day', 'revenue_per_min', 'is_weekend']].head())