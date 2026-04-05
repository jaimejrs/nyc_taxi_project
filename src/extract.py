import pandas as pd
import os

def load_data(file_path):
    """
    Lê o arquivo CSV e retorna um DataFrame.
    """
    print(f"Iniciando a leitura de: {file_path}")
    
    try:
        df = pd.read_csv(file_path, low_memory=False)
        print("Carga concluída com sucesso!")
        return df
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        return None

def inspect_data(df):
    """
    Realiza a inspeção inicial da estrutura dos dados.
    """
    print("\n--- Estrutura do Dataset ---")
    print(df.info()) 
    
    print("\n--- Primeiras 5 linhas ---")
    print(df.head())
    
    print("\n--- Estatísticas Descritivas ---")
    print(df.describe())

if __name__ == "__main__":
    DATA_PATH = "data/raw/yellow_tripdata_2015-01.csv"
    
    if os.path.exists(DATA_PATH):
        taxi_df = load_data(DATA_PATH)
        if taxi_df is not None:
            inspect_data(taxi_df)
    else:
        print(f"Arquivo não encontrado em: {DATA_PATH}. Certifique-se de baixar o dataset do Kaggle.")