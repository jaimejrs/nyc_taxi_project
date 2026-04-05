import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# 1. Configuração da página
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NYC Taxi Analytics",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Paleta de cores
# ─────────────────────────────────────────────
COLORS = {
    "yellow":  "#F5C518",
    "blue":    "#1C6EF7",
    "green":   "#22C55E",
    "red":     "#EF4444",
    "purple":  "#A855F7",
    "orange":  "#F97316",
    "teal":    "#14B8A6",
    "gray":    "#6B7280",
}

SHIFT_ORDER   = ["madrugada", "manhã", "tarde", "noite"]
SHIFT_COLORS  = ["#6366F1", "#F59E0B", "#10B981", "#3B82F6"]

PAYMENT_MAP   = {1: "Cartão de Crédito", 2: "Dinheiro",
                 3: "Sem Cobrança",      4: "Disputa",     5: "Desconhecido"}
MONTH_MAP     = {
    "2015-01": "Jan 2015",
    "2016-01": "Jan 2016",
    "2016-02": "Fev 2016",
    "2016-03": "Mar 2016",
}
DAY_MAP       = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# ─────────────────────────────────────────────
# 2. Carregamento dos dados
# ─────────────────────────────────────────────
@st.cache_data
def load_aggregated_data():
    df_daily = pd.read_parquet("data/processed/agg_daily.parquet")
    df_daily["pickup_date"] = pd.to_datetime(df_daily["pickup_date_str"])
    df_daily["Mês"] = df_daily["pickup_date"].dt.strftime("%Y-%m")
    df_daily = df_daily.sort_values("pickup_date")

    df_shift = pd.read_parquet("data/processed/agg_shift.parquet")
    df_shift["payment_label"] = df_shift["payment_type"].map(PAYMENT_MAP)
    df_shift["time_of_day"] = pd.Categorical(
        df_shift["time_of_day"], categories=SHIFT_ORDER, ordered=True
    )
    return df_daily, df_shift

@st.cache_data
def load_extra_aggs():
    out = {}
    try:
        df = pd.read_parquet("data/processed/agg_percentiles.parquet")
        out["percentiles"] = df
    except FileNotFoundError:
        out["percentiles"] = None

    try:
        df = pd.read_parquet("data/processed/agg_weekend.parquet")
        out["weekend"] = df
    except FileNotFoundError:
        out["weekend"] = None

    try:
        df = pd.read_parquet("data/processed/agg_heatmap.parquet")
        out["heatmap"] = df
    except FileNotFoundError:
        out["heatmap"] = None

    return out

@st.cache_data
def load_detailed_sample():
    """Carrega amostra do dado detalhado (2015-01) para mapa e anomalias."""
    df = pd.read_parquet("data/processed/yellow_tripdata_2015-01.parquet")
    return df.sample(15_000, random_state=42)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def fmt_brl(n, prefix="", suffix=""):
    """Formata número no padrão brasileiro."""
    return f"{prefix}{n:,.2f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_int(n):
    return f"{n:,.0f}".replace(",", ".")

FONT_STYLE = dict(family="Inter, sans-serif", size=13, color="#374151")

def plotly_defaults():
    """Returns kwargs safe to pass directly to plotly.express functions."""
    return dict(template="plotly_white")

def apply_font(fig):
    """Applies standard font styling via update_layout (not supported as px kwarg)."""
    fig.update_layout(font=FONT_STYLE)
    return fig

# ─────────────────────────────────────────────
# 3. Carrega dados
# ─────────────────────────────────────────────
try:
    with st.spinner("Carregando dados…"):
        df_daily, df_shift = load_aggregated_data()
        extra = load_extra_aggs()
        df_detailed = load_detailed_sample()

    all_months = sorted(df_daily["Mês"].unique())

    # ─────────────────────────────────────────────
    # 4. Sidebar — Filtros Globais
    # ─────────────────────────────────────────────
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/NYC_Taxi_2011.jpg/320px-NYC_Taxi_2011.jpg",
                 use_container_width=True)
        st.markdown("## 🚕 NYC Taxi Analytics")
        st.markdown("---")

        st.markdown("### 📅 Período")
        meses_sel = st.multiselect(
            "Selecione os meses",
            options=all_months,
            default=all_months,
            format_func=lambda m: MONTH_MAP.get(m, m),
        )
        if not meses_sel:
            meses_sel = all_months

        st.markdown("### ⏰ Turno do Dia")
        turnos_sel = st.multiselect(
            "Selecione os turnos",
            options=SHIFT_ORDER,
            default=SHIFT_ORDER,
        )
        if not turnos_sel:
            turnos_sel = SHIFT_ORDER

        st.markdown("### 💳 Tipo de Pagamento")
        pay_opts = list(PAYMENT_MAP.values())
        pay_sel  = st.multiselect(
            "Selecione os tipos",
            options=pay_opts,
            default=pay_opts,
        )
        if not pay_sel:
            pay_sel = pay_opts

        st.markdown("---")
        st.caption("Dados: NYC TLC Yellow Taxi  \n**Jan 2015 · Jan–Mar 2016**")

    # ─────────────────────────────────────────────
    # 5. Filtros aplicados
    # ─────────────────────────────────────────────
    df_filt = df_daily[df_daily["Mês"].isin(meses_sel)].copy()
    df_shift_filt = df_shift[
        df_shift["time_of_day"].isin(turnos_sel) &
        df_shift["payment_label"].isin(pay_sel)
    ].copy()

    # ─────────────────────────────────────────────
    # 6. Header
    # ─────────────────────────────────────────────
    st.markdown(
        "<h1 style='margin-bottom:0'>🚕 NYC Yellow Taxi — Dashboard Analítico</h1>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"Exibindo **{fmt_int(len(meses_sel))} mês(es)** · "
        f"Período: {pd.to_datetime(df_filt['pickup_date'].min()).strftime('%d/%m/%Y')} a "
        f"{pd.to_datetime(df_filt['pickup_date'].max()).strftime('%d/%m/%Y')}"
    )
    st.divider()

    # ─────────────────────────────────────────────
    # 7. Abas
    # ─────────────────────────────────────────────
    tab_exec, tab_fin, tab_oper, tab_geo, tab_anom = st.tabs([
        "📊 Visão Executiva",
        "💰 Visão Financeira",
        "⚙️ Visão Operacional",
        "🗺️ Visão Geográfica",
        "🚨 Anomalias",
    ])

    # ═══════════════════════════════════════════
    # ABA 1: VISÃO EXECUTIVA
    # ═══════════════════════════════════════════
    with tab_exec:

        # --- KPIs com delta ---
        total_trips   = df_filt["total_trips"].sum()
        total_rev     = df_filt["total_revenue"].sum()
        avg_fare      = df_filt["avg_fare"].mean()
        avg_tip_pct   = df_filt["avg_tip_pct"].mean() * 100

        # delta: último mês vs penúltimo (se disponível)
        sorted_months = sorted(meses_sel)
        if len(sorted_months) >= 2:
            prev_m   = df_filt[df_filt["Mês"] == sorted_months[-2]]
            curr_m   = df_filt[df_filt["Mês"] == sorted_months[-1]]
            d_trips  = int(curr_m["total_trips"].sum() - prev_m["total_trips"].sum())
            d_rev    = curr_m["total_revenue"].sum() - prev_m["total_revenue"].sum()
            d_fare   = curr_m["avg_fare"].mean()     - prev_m["avg_fare"].mean()
            d_tip    = (curr_m["avg_tip_pct"].mean() - prev_m["avg_tip_pct"].mean()) * 100
        else:
            d_trips = d_rev = d_fare = d_tip = None

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🚖 Total de Corridas",
                    fmt_int(total_trips),
                    delta=fmt_int(d_trips) if d_trips is not None else None)
        col2.metric("💵 Receita Total (USD)",
                    f"$ {fmt_brl(total_rev)}",
                    delta=f"$ {fmt_brl(d_rev)}" if d_rev is not None else None)
        col3.metric("🎫 Ticket Médio (USD)",
                    f"$ {avg_fare:.2f}",
                    delta=f"{d_fare:+.2f}" if d_fare is not None else None)
        col4.metric("💡 Gorjeta Média",
                    f"{avg_tip_pct:.1f} %",
                    delta=f"{d_tip:+.1f} %" if d_tip is not None else None)

        st.divider()

        # --- Gráfico de volume diário interativo ---
        col_a, col_b = st.columns(2)

        with col_a:
            fig_vol = px.line(
                df_filt, x="pickup_date", y="total_trips",
                title="Volume de Corridas por Dia",
                labels={"pickup_date": "Data", "total_trips": "Corridas"},
                color_discrete_sequence=[COLORS["blue"]],
                **plotly_defaults(),
            )
            fig_vol.update_traces(line_width=1.8)
            apply_font(fig_vol).update_layout(height=320, title_font_size=15)
            st.plotly_chart(fig_vol, use_container_width=True)

        with col_b:
            fig_fare = px.area(
                df_filt, x="pickup_date", y="avg_fare",
                title="Evolução do Ticket Médio Diário (USD)",
                labels={"pickup_date": "Data", "avg_fare": "Ticket Médio ($)"},
                color_discrete_sequence=[COLORS["yellow"]],
                **plotly_defaults(),
            )
            apply_font(fig_fare).update_layout(height=320, title_font_size=15)
            st.plotly_chart(fig_fare, use_container_width=True)

        st.divider()

        # --- Comparativo Dia Útil vs Fim de Semana ---
        st.subheader("📆 Dia Útil vs Fim de Semana")

        wknd_data = extra.get("weekend")
        if wknd_data is not None:
            wk_filt = wknd_data[wknd_data["month"].isin(meses_sel)]
            wk_grouped = wk_filt.groupby("is_weekend").agg(
                total_trips=("total_trips", "sum"),
                avg_fare=("avg_fare", "mean"),
                avg_tip_pct=("avg_tip_pct", "mean"),
                avg_distance=("avg_distance", "mean"),
                avg_duration=("avg_duration", "mean"),
                avg_revenue_per_min=("avg_revenue_per_min", "mean"),
            ).reset_index()
            wk_grouped["Tipo"] = wk_grouped["is_weekend"].map({False: "Dia Útil", True: "Fim de Semana"})

            wk_col1, wk_col2, wk_col3 = st.columns(3)
            metrics_wk = [
                ("avg_fare",           "Ticket Médio ($)",       wk_col1),
                ("avg_tip_pct",        "Gorjeta Média (%)",      wk_col2),
                ("avg_revenue_per_min","Receita / Minuto ($)",   wk_col3),
            ]
            for field, title, col in metrics_wk:
                scale = 100 if "pct" in field else 1
                fig = px.bar(
                    wk_grouped, x="Tipo", y=field,
                    title=title, text_auto=".2f",
                    color="Tipo",
                    color_discrete_map={"Dia Útil": COLORS["blue"], "Fim de Semana": COLORS["orange"]},
                    **plotly_defaults(),
                )
                apply_font(fig).update_layout(height=280, showlegend=False, title_font_size=13)
                fig.update_traces(textposition="outside")
                col.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Agregação de fim de semana ainda não gerada. Rode o script de agregações auxiliares.")

    # ═══════════════════════════════════════════
    # ABA 2: VISÃO FINANCEIRA
    # ═══════════════════════════════════════════
    with tab_fin:
        st.subheader("Análise de Receita e Pagamentos")

        fin_col1, fin_col2 = st.columns(2)

        with fin_col1:
            pay_pivot = df_shift_filt.pivot_table(
                index="time_of_day", columns="payment_label",
                values="total_revenue", aggfunc="sum"
            ).fillna(0).reset_index()
            pay_pivot["time_of_day"] = pd.Categorical(
                pay_pivot["time_of_day"], categories=SHIFT_ORDER, ordered=True
            )
            pay_pivot = pay_pivot.sort_values("time_of_day")

            pay_cols = [c for c in pay_pivot.columns if c != "time_of_day"]
            fig_stacked = go.Figure()
            for col_name in pay_cols:
                fig_stacked.add_trace(go.Bar(name=col_name, x=pay_pivot["time_of_day"], y=pay_pivot[col_name]))
            fig_stacked.update_layout(
                barmode="stack",
                title="Receita por Turno e Tipo de Pagamento",
                xaxis_title="Turno",
                yaxis_title="Receita (USD)",
                height=340,
                template="plotly_white",
                font=FONT_STYLE,
            )
            st.plotly_chart(fig_stacked, use_container_width=True)

        with fin_col2:
            pay_totals = df_shift_filt.groupby("payment_label")["total_revenue"].sum().reset_index()
            pay_totals = pay_totals.sort_values("total_revenue", ascending=False)
            fig_pay = px.bar(
                pay_totals, x="payment_label", y="total_revenue",
                title="Receita Total por Tipo de Pagamento",
                labels={"payment_label": "Tipo de Pagamento", "total_revenue": "Receita (USD)"},
                color="payment_label",
                color_discrete_sequence=px.colors.qualitative.Safe,
                text_auto=".3s",
                **plotly_defaults(),
            )
            apply_font(fig_pay).update_layout(height=340, showlegend=False)
            fig_pay.update_traces(textposition="outside")
            st.plotly_chart(fig_pay, use_container_width=True)

        st.divider()

        # --- % de corridas por turno e pagamento (heatmap) ---
        st.subheader("🔥 Distribuição de Corridas (%)")
        hm_pivot = df_shift_filt.pivot_table(
            index="time_of_day", columns="payment_label",
            values="pct_trips", aggfunc="sum"
        ).fillna(0)
        try:
            hm_pivot = hm_pivot.loc[
                [t for t in SHIFT_ORDER if t in hm_pivot.index]
            ]
        except Exception:
            pass

        fig_hm = px.imshow(
            hm_pivot,
            text_auto=".1f",
            color_continuous_scale="Blues",
            title="% Corridas: Turno × Tipo de Pagamento",
            labels={"x": "Pagamento", "y": "Turno", "color": "%"},
            **plotly_defaults(),
        )
        apply_font(fig_hm).update_layout(height=300)
        st.plotly_chart(fig_hm, use_container_width=True)

        # --- Rentabilidade ---
        st.divider()
        st.subheader("📈 Análise de Rentabilidade")

        rnt_col1, rnt_col2 = st.columns(2)

        with rnt_col1:
            # Scatter: distância vs receita (amostra detalhada)
            df_scat = df_detailed[
                (df_detailed["trip_distance"] > 0) &
                (df_detailed["total_amount"]  > 0) &
                (df_detailed["trip_distance"] < 30)
            ].sample(min(3000, len(df_detailed)), random_state=1)

            df_scat["time_of_day_str"] = df_scat["time_of_day"].astype(str)
            fig_scat = px.scatter(
                df_scat,
                x="trip_distance", y="total_amount",
                color="time_of_day_str",
                title="Distância × Receita Total (amostra)",
                labels={
                    "trip_distance": "Distância (mi)",
                    "total_amount":  "Receita ($)",
                    "time_of_day_str": "Turno",
                },
                color_discrete_map=dict(zip(SHIFT_ORDER, SHIFT_COLORS)),
                opacity=0.45,
                **plotly_defaults(),
            )
            apply_font(fig_scat).update_layout(height=360)
            st.plotly_chart(fig_scat, use_container_width=True)

        with rnt_col2:
            # Box plot: revenue_per_mile por turno
            df_box = df_detailed[
                (df_detailed["revenue_per_mile"] > 0) &
                (df_detailed["revenue_per_mile"] < 30)
            ].copy()
            df_box["time_of_day_str"] = pd.Categorical(
                df_box["time_of_day"].astype(str), categories=SHIFT_ORDER, ordered=True
            )
            fig_box = px.box(
                df_box.sort_values("time_of_day_str"),
                x="time_of_day_str", y="revenue_per_mile",
                color="time_of_day_str",
                title="Receita por Milha · Distribuição por Turno",
                labels={
                    "time_of_day_str":  "Turno",
                    "revenue_per_mile": "Receita / Milha ($)",
                },
                color_discrete_map=dict(zip(SHIFT_ORDER, SHIFT_COLORS)),
                **plotly_defaults(),
            )
            apply_font(fig_box).update_layout(height=360, showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

    # ═══════════════════════════════════════════
    # ABA 3: VISÃO OPERACIONAL
    # ═══════════════════════════════════════════
    with tab_oper:
        st.subheader("Métricas Operacionais")

        # --- Heatmap hora × dia da semana ---
        hm_raw = extra.get("heatmap")
        if hm_raw is not None:
            hm_f = hm_raw[hm_raw["month"].isin(meses_sel)]
            hm_agg = hm_f.groupby(["day_of_week", "hour"])["total_trips"].sum().reset_index()
            hm_pivot2 = hm_agg.pivot(index="day_of_week", columns="hour", values="total_trips").fillna(0)
            hm_pivot2.index = [DAY_MAP[i] for i in hm_pivot2.index]

            fig_hw = px.imshow(
                hm_pivot2,
                color_continuous_scale="YlOrRd",
                title="🔥 Mapa de Calor — Demanda por Hora × Dia da Semana",
                labels={"x": "Hora do Dia", "y": "Dia da Semana", "color": "Corridas"},
                text_auto=False,
                aspect="auto",
                **plotly_defaults(),
            )
            apply_font(fig_hw).update_layout(height=320)
            st.plotly_chart(fig_hw, use_container_width=True)
        else:
            st.info("Agregação de heatmap ainda não disponível.")

        st.divider()

        # --- Distribuições Estatísticas ---
        st.subheader("📊 Distribuições & Percentis")

        dist_col1, dist_col2 = st.columns(2)

        with dist_col1:
            fig_hist_dur = px.histogram(
                df_detailed[df_detailed["trip_duration_min"].between(1, 60)],
                x="trip_duration_min", nbins=40,
                title="Distribuição de Duração das Corridas (min)",
                labels={"trip_duration_min": "Duração (min)", "count": "Corridas"},
                color_discrete_sequence=[COLORS["blue"]],
                **plotly_defaults(),
            )
            apply_font(fig_hist_dur).update_layout(height=300)
            st.plotly_chart(fig_hist_dur, use_container_width=True)

        with dist_col2:
            fig_hist_dist = px.histogram(
                df_detailed[df_detailed["trip_distance"].between(0.1, 20)],
                x="trip_distance", nbins=40,
                title="Distribuição de Distância das Corridas (mi)",
                labels={"trip_distance": "Distância (mi)", "count": "Corridas"},
                color_discrete_sequence=[COLORS["teal"]],
                **plotly_defaults(),
            )
            apply_font(fig_hist_dist).update_layout(height=300)
            st.plotly_chart(fig_hist_dist, use_container_width=True)

        # Percentis
        perc_data = extra.get("percentiles")
        if perc_data is not None:
            perc_filt = perc_data[perc_data["month"].isin(meses_sel)]
            perc_agg  = perc_filt.groupby("percentile")[
                ["trip_duration_min", "trip_distance", "fare_amount"]
            ].mean().reset_index()
            perc_agg.columns = ["Percentil", "Duração Média (min)", "Distância Média (mi)", "Tarifa Média ($)"]
            perc_agg = perc_agg.set_index("Percentil")

            st.markdown("#### Percentis consolidados (P25 · P50 · P75 · P90 · P95)")
            st.dataframe(
                perc_agg.style.format("{:.2f}").background_gradient(cmap="Blues"),
                use_container_width=True,
            )
        else:
            st.info("Rode o script de agregações auxiliares para ver os percentis.")

        st.divider()

        # --- Tabela de operações diárias ---
        st.subheader("📋 Métricas Diárias Detalhadas")
        oper_display = df_filt[[
            "pickup_date", "Mês", "total_trips", "avg_distance", "avg_duration"
        ]].copy()
        oper_display.columns = ["Data", "Mês/Ano", "Total de Corridas", "Distância Média (mi)", "Duração Média (min)"]
        oper_display["Data"] = oper_display["Data"].dt.strftime("%d/%m/%Y")
        st.dataframe(
            oper_display.sort_values("Data", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    # ═══════════════════════════════════════════
    # ABA 4: VISÃO GEOGRÁFICA
    # ═══════════════════════════════════════════
    with tab_geo:
        st.subheader("🗺️ Mapa de Demanda — Origem das Corridas")
        st.markdown("Visualize a concentração de corridas por hora do dia usando o mapa de calor geográfico (Jan 2015).")

        hora_sel = st.slider("Filtre pela Hora do Dia (0 a 23h)", 0, 23, 12, 1)

        df_map = df_detailed[
            df_detailed["pickup_datetime"].dt.hour == hora_sel
        ].copy()
        df_map = df_map.rename(columns={"pickup_latitude": "lat", "pickup_longitude": "lon"})
        df_map = df_map[["lat", "lon"]].dropna()
        df_map = df_map[
            df_map["lat"].between(40.4, 41.0) &
            df_map["lon"].between(-74.3, -73.6)
        ]

        geo_col1, geo_col2 = st.columns([3, 1])

        with geo_col1:
            if len(df_map) > 0:
                try:
                    import pydeck as pdk
                    layer = pdk.Layer(
                        "HeatmapLayer",
                        data=df_map,
                        get_position="[lon, lat]",
                        aggregation=pdk.types.String("MEAN"),
                        get_weight=1,
                        radius_pixels=35,
                        intensity=1,
                        threshold=0.03,
                        color_range=[
                            [0, 25, 180, 0],
                            [0, 100, 220, 180],
                            [0, 200, 150, 200],
                            [255, 200, 0, 220],
                            [255, 80, 0, 240],
                            [255, 0, 0, 255],
                        ],
                    )
                    view = pdk.ViewState(
                        latitude=40.72, longitude=-73.98,
                        zoom=11, pitch=0,
                    )
                    deck = pdk.Deck(
                        layers=[layer],
                        initial_view_state=view,
                        map_style="mapbox://styles/mapbox/dark-v10",
                    )
                    st.pydeck_chart(deck, use_container_width=True, height=480)
                except Exception:
                    st.map(df_map[["lat", "lon"]], use_container_width=True)
            else:
                st.warning("Nenhuma corrida na amostra para esse horário.")

        with geo_col2:
            st.markdown(f"**Hora selecionada:** `{hora_sel}:00`")
            st.metric("Corridas nessa hora", fmt_int(len(df_map)))
            pct = len(df_map) / len(df_detailed) * 100
            st.metric("% da amostra", f"{pct:.1f} %")

            st.markdown("---")
            top_dist = df_detailed[
                df_detailed["pickup_datetime"].dt.hour == hora_sel
            ]["distance_range"].value_counts().reset_index()
            top_dist.columns = ["Faixa", "Corridas"]
            top_dist["Faixa"] = top_dist["Faixa"].astype(str)
            st.markdown("**Faixas de distância**")
            st.dataframe(top_dist, use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════════
    # ABA 5: ANOMALIAS
    # ═══════════════════════════════════════════
    with tab_anom:
        st.subheader("🚨 Corridas Suspeitas para Investigação")

        df_anom = df_detailed[df_detailed["anomaly_flag"] == True].copy()
        total_rev_sample = df_detailed["total_amount"].sum()
        anom_rev = df_anom["total_amount"].sum() if len(df_anom) > 0 else 0

        # KPIs de impacto
        a1, a2, a3 = st.columns(3)
        a1.metric("⚠️ Anomalias na Amostra",  fmt_int(len(df_anom)))
        a2.metric("💸 Receita nas Anomalias", f"$ {anom_rev:.2f}")
        a3.metric("📉 % da Receita da Amostra",
                  f"{(anom_rev / total_rev_sample * 100):.4f} %")

        if len(df_anom) > 0:
            st.warning(
                f"Critério: velocidade estimada > 80 mph **E** tarifa < $ 5,00. "
                f"Encontradas **{len(df_anom)} corridas** suspeitas na amostra de {fmt_int(len(df_detailed))} registros."
            )

            anom_col1, anom_col2 = st.columns(2)

            with anom_col1:
                # Distribuição de anomalias por turno
                df_anom["time_of_day_str"] = df_anom["time_of_day"].astype(str)
                anom_turno = df_anom["time_of_day_str"].value_counts().reset_index()
                anom_turno.columns = ["Turno", "Anomalias"]
                fig_anom = px.bar(
                    anom_turno, x="Turno", y="Anomalias",
                    title="Anomalias por Turno do Dia",
                    color="Turno",
                    color_discrete_map=dict(zip(SHIFT_ORDER, SHIFT_COLORS)),
                    **plotly_defaults(),
                )
                apply_font(fig_anom).update_layout(height=300, showlegend=False)
                st.plotly_chart(fig_anom, use_container_width=True)

            with anom_col2:
                # Scatter das anomalias: distância vs duração
                speed = df_anom["trip_distance"] / (df_anom["trip_duration_min"] / 60).replace(0, np.nan)
                df_anom = df_anom.copy()
                df_anom["speed_mph"] = speed

                fig_anom_scat = px.scatter(
                    df_anom,
                    x="trip_distance", y="trip_duration_min",
                    size="total_amount",
                    color="speed_mph",
                    color_continuous_scale="Reds",
                    title="Distância × Duração das Anomalias (tamanho = total $)",
                    labels={
                        "trip_distance":    "Distância (mi)",
                        "trip_duration_min":"Duração (min)",
                        "speed_mph":        "Velocidade (mph)",
                    },
                    **plotly_defaults(),
                )
                apply_font(fig_anom_scat).update_layout(height=300)
                st.plotly_chart(fig_anom_scat, use_container_width=True)

            st.markdown("#### Registros Detalhados")
            cols_disp = ["pickup_datetime", "trip_distance", "trip_duration_min",
                         "fare_amount", "total_amount", "time_of_day"]
            df_anom_disp = df_anom[cols_disp].copy()
            df_anom_disp["time_of_day"] = df_anom_disp["time_of_day"].astype(str)
            df_anom_disp.columns = [
                "Data/Hora Início", "Distância (mi)", "Duração (min)",
                "Tarifa ($)", "Total ($)", "Turno",
            ]
            st.dataframe(df_anom_disp, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Nenhuma anomalia encontrada nesta amostra!")

except FileNotFoundError as e:
    st.error(f"Arquivo não encontrado: {e}  \nVerifique a pasta `data/processed/`.")