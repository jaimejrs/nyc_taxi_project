import os
import pandas as pd

from extract import load_data
from validate import validate_data
from transform import transform_data
from aggregate import aggregate_by_day, aggregate_by_shift_payment, calculate_percentiles

def run_pipeline():
    """
    Executa o pipeline ETL completo processando os arquivos em lote.
    """
    input_dir = "data/raw/"
    output_dir = "data/processed/"
    os.makedirs(output_dir, exist_ok=True)

    # Lista dos arquivos para processar
    files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    
    # Ordenar a lista 
    files.sort()
    
    if not files:
        print(f"Nenhum arquivo .csv encontrado na pasta {input_dir}.")
        return

    all_daily_agg = []
    all_shift_agg = []
    
    for file_name in files:
        file_path = os.path.join(input_dir, file_name)
        if not os.path.exists(file_path):
            print(f"Arquivo não encontrado: {file_path}. Pulando...")
            continue
        
        print(f"\n{'='*50}")
        print(f"Iniciando processamento de: {file_name}")
        print(f"{'='*50}")

        # 1. Extract
        df_raw = load_data(file_path)
        if df_raw is None:
            continue

        # Extraindo o lote (ano-mês) do nome do arquivo para a validação temporal
        year_month = file_name.replace("yellow_tripdata_", "").replace(".csv", "")

        # 2. Validate
        df_clean, score = validate_data(df_raw, year_month)

        # 3. Transform
        df_transformed = transform_data(df_clean)

        # 4. Agregações 
        df_daily = aggregate_by_day(df_transformed)
        df_shift = aggregate_by_shift_payment(df_transformed)
        
        all_daily_agg.append(df_daily)
        all_shift_agg.append(df_shift)

        # 5. Load 
        parquet_filename = file_name.replace(".csv", ".parquet")
        output_file = os.path.join(output_dir, parquet_filename)
        
        print(f"Salvando dados processados em: {output_file}")
        df_transformed.to_parquet(output_file, engine='pyarrow', index=False)
        print(f"Lote {year_month} concluído com sucesso!")

    # Salvando as agregações consolidadas para uso rápido no Streamlit
    if all_daily_agg:
        print("\nConsolidando e salvando métricas agregadas...")
        final_daily = pd.concat(all_daily_agg, ignore_index=True)
        final_shift = pd.concat(all_shift_agg, ignore_index=True)
        
        final_daily.to_parquet(os.path.join(output_dir, "agg_daily.parquet"), engine='pyarrow', index=False)
        final_shift.to_parquet(os.path.join(output_dir, "agg_shift.parquet"), engine='pyarrow', index=False)
        
    print("\nPipeline ETL finalizado com sucesso!")

if __name__ == "__main__":
    run_pipeline()