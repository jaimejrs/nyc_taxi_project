# 🚕 NYC Yellow Taxi — Projeto de Análise de Dados

Análise exploratória e dashboard interativo das corridas de táxi amarelo de Nova York.
Cobre o período de **Janeiro 2015** e **Janeiro–Março 2016** (~45 milhões de registros).

---

## 📁 Estrutura do Projeto

```
nyc_taxi_project/
├── data/
│   ├── raw/                  # CSVs originais (não versionados)
│   └── processed/            # Parquets gerados pelo pipeline ETL
├── src/
│   ├── extract.py            # Leitura dos CSVs
│   ├── validate.py           # Validação de qualidade (7 regras + quality score)
│   ├── transform.py          # Feature engineering (duração, turnos, rentabilidade…)
│   ├── aggregate.py          # Agregações diárias, por turno, percentis, rotas
│   └── database.py           # Orquestrador do pipeline ETL completo
├── dashboard.py              # Dashboard Streamlit interativo
├── requirements.txt
└── .gitignore
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
- Python 3.10+
- Dados raw na pasta `data/raw/` (baixar do [Kaggle NYC TLC](https://www.kaggle.com/datasets/elemento/nyc-yellow-cab))

### 2. Criar ambiente virtual e instalar dependências
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Rodar o pipeline ETL
Gera todos os parquets em `data/processed/`:
```bash
cd src
python database.py
```

### 4. Gerar agregações auxiliares
Gera heatmaps, percentis e comparativo fim de semana:
```bash
# Rodar o script de agregações auxiliares (veja seção abaixo)
python agg_aux.py
```

### 5. Iniciar o dashboard
```bash
streamlit run dashboard.py
```
Acesse em [http://localhost:8501](http://localhost:8501)

---

## 📊 Features do Dashboard

| Aba | Conteúdo |
|-----|----------|
| 📊 Visão Executiva | KPIs com delta mês a mês, volume diário, ticket médio, comparativo dia útil vs fim de semana |
| 💰 Visão Financeira | Receita por turno/pagamento, heatmap de distribuição, scatter de rentabilidade, box plot por turno |
| ⚙️ Visão Operacional | Heatmap hora × dia da semana, distribuições histograma, percentis P25–P95, tabela diária |
| 🗺️ Visão Geográfica | Heatmap geográfico (pydeck) filtrado por hora do dia |
| 🚨 Anomalias | KPIs de impacto financeiro, distribuição por turno, scatter de corridas suspeitas |

### Filtros Globais (Sidebar)
- **Mês/Período** — selecione um ou mais dos 4 meses disponíveis
- **Turno do Dia** — madrugada, manhã, tarde, noite
- **Tipo de Pagamento** — Cartão de Crédito, Dinheiro, Sem Cobrança, Disputa

---

## 🗂️ Dataset

| Arquivo | Período | Registros |
|---------|---------|-----------|
| `yellow_tripdata_2015-01` | Jan 2015 | ~11,7 M |
| `yellow_tripdata_2016-01` | Jan 2016 | ~10,6 M |
| `yellow_tripdata_2016-02` | Fev 2016 | ~11,1 M |
| `yellow_tripdata_2016-03` | Mar 2016 | ~11,9 M |
| **Total** | | **~45,4 M** |

---

## ✅ Pipeline de Validação

O módulo `validate.py` aplica 7 regras de qualidade:
1. Verificação de nulos
2. Coordenadas dentro dos limites de NYC
3. Ranges plausíveis (distância, passageiros, tarifa)
4. Consistência financeira (total ≈ soma dos componentes)
5. Integridade temporal (mês correto, dropoff > pickup)
6. Domínio de categorias de pagamento
7. Detecção de duplicatas

O **Quality Score** (0–100) é calculado e impresso para cada lote.
