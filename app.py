import streamlit as st
import pandas as pd
from pathlib import Path
from streamlit_echarts import st_echarts

# ================== CONFIG ==================
st.set_page_config(page_title="Aging - Filtros", layout="wide")

# Ocultar cabecera/menú/footer + tarjetas compactas + títulos de mini-tablas
st.markdown(
    """
    <style>
      header {visibility: hidden;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .block-container { padding-top: 0.5rem; }

      /* Tarjetas métricas (compactas) */
      .metric-card {
          border-radius: 12px;
          padding: 8px 10px;
          box-shadow: 0 1px 6px rgba(0,0,0,0.05);
          border: 1px solid rgba(0,0,0,0.05);
          display: inline-block;
          margin: 0 6px 6px 0;
          min-width: 120px;
          vertical-align: top;
      }
      .metric-label { font-size: 10px; opacity: 0.7; margin-bottom: 2px; }
      .metric-value { font-size: 16px; font-weight: 700; line-height: 1.1; }

      .mini-title { font-weight: 600; margin: 0 0 6px 2px; }
    </style>
    """,
    unsafe_allow_html=True
)

# Columnas requeridas
REQUIRED_COLUMNS = [
    "BUKRS_TXT", "KUNNR_TXT", "PRCTR", "VKORG_TXT", "VTWEG_TXT",
    "NOT_DUE_AMOUNT_USD", "DUE_30_DAYS_USD", "DUE_60_DAYS_USD", "DUE_90_DAYS_USD",
    "DUE_120_DAYS_USD", "DUE_180_DAYS_USD", "DUE_270_DAYS_USD", "DUE_360_DAYS_USD", "DUE_OVER_360_DAYS_USD"
]

metric_cols = [
    "NOT_DUE_AMOUNT_USD", "DUE_30_DAYS_USD", "DUE_60_DAYS_USD", "DUE_90_DAYS_USD",
    "DUE_120_DAYS_USD", "DUE_180_DAYS_USD", "DUE_270_DAYS_USD", "DUE_360_DAYS_USD", "DUE_OVER_360_DAYS_USD"
]

# ================== CARGA DE DATOS ==================
@st.cache_data(show_spinner=False)
def load_excel(path_or_buffer):
    df = pd.read_excel(path_or_buffer)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = None
default_path = Path("AGING AL 2025-01-28.xlsx")

with st.sidebar:
    st.markdown("**Archivo**")
    up = st.file_uploader("Subí un .xlsx", type=["xlsx"], label_visibility="collapsed")
    if up is not None:
        try:
            df = load_excel(up)
        except Exception as e:
            st.error(f"No se pudo leer el Excel subido: {e}")

if df is None and default_path.exists():
    try:
        df = load_excel(default_path)
    except Exception as e:
        st.error(f"No se pudo leer el Excel por defecto: {e}")

if df is None:
    st.info("Cargá un archivo Excel (xlsx) desde la barra izquierda.")
    st.stop()

# Validar columnas
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas en el Excel: {', '.join(missing)}")
    st.stop()

# ================== PARSEO NUMÉRICO ==================
def smart_to_numeric(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.fillna(0)
    s1 = pd.to_numeric(s, errors="coerce")
    if s1.isna().mean() > 0.5:
        s2 = (
            s.astype(str)
             .str.replace(r"\.", "", regex=True)
             .str.replace(",", ".", regex=False)
        )
        s1 = pd.to_numeric(s2, errors="coerce")
    return s1.fillna(0)

for col in metric_cols:
    df[f"_{col}_NUM"] = smart_to_numeric(df[col])

# ================== CONTROL DE RESETEO ==================
if "filters_version" not in st.session_state:
    st.session_state["filters_version"] = 0
filters_version = st.session_state["filters_version"]

# ================== SIDEBAR DE FILTROS ==================
with st.sidebar:
    st.markdown("**Filtros**")

    def dropdown(label, colname):
        vals = pd.Series(df[colname].dropna().unique())
        try:
            vals = vals.sort_values()
        except Exception:
            pass
        options = ["Todos"] + vals.astype(str).tolist()
        key = f"sel_{colname}_{filters_version}"
        return st.selectbox(label, options=options, index=0, key=key)

    sel_BUKRS_TXT = dropdown("Sociedad", "BUKRS_TXT")
    sel_KUNNR_TXT = dropdown("Cliente",  "KUNNR_TXT")
    sel_PRCTR     = dropdown("Cen.Ben",  "PRCTR")
    sel_VKORG_TXT = dropdown("Mercado",  "VKORG_TXT")
    sel_VTWEG_TXT = dropdown("Canal",    "VTWEG_TXT")

    if st.button("🧹 Limpiar filtros", use_container_width=True):
        st.session_state["filters_version"] += 1

# ================== BASE PARA TARJETAS ==================
df_for_metrics = df if sel_KUNNR_TXT == "Todos" else df[df["KUNNR_TXT"].astype(str) == str(sel_KUNNR_TXT)]

# ================== TARJETAS (compactas, en millones; nombres originales) ==================
def format_usd_millions(x: float) -> str:
    millones = x / 1_000_000
    return f"US$ {millones:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")

cards_html = ""
for col in metric_cols:
    val = df_for_metrics[f"_{col}_NUM"].sum()
    cards_html += f"""
    <div class="metric-card">
        <div class="metric-label">{col}</div>
        <div class="metric-value">{format_usd_millions(val)}</div>
    </div>
    """
st.markdown(cards_html, unsafe_allow_html=True)

# ================== PIE CHART ==================
label_map = {
    "NOT_DUE_AMOUNT_USD": "No vencido",
    "DUE_30_DAYS_USD": "30",
    "DUE_60_DAYS_USD": "60",
    "DUE_90_DAYS_USD": "90",
    "DUE_120_DAYS_USD": "120",
    "DUE_180_DAYS_USD": "180",
    "DUE_270_DAYS_USD": "270",
    "DUE_360_DAYS_USD": "360",
    "DUE_OVER_360_DAYS_USD": "+360",
}
reverse_label_map = {v: k for k, v in label_map.items()}

col_sums = {col: float(df_for_metrics[f"_{col}_NUM"].sum()) for col in metric_cols}
pie_data = [{"name": label_map.get(k, k), "value": float(v)} for k, v in col_sums.items() if v > 0]

echarts_colors = ["#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE",
                  "#3BA272", "#FC8452", "#9A60B4", "#EA7CCC"]

# ⚠️ Hacemos las tablas MÁS ANCHAS: el área de tablas ahora es más grande que antes.
col_chart, col_tables = st.columns([3, 2])  # antes [2,1]

with col_chart:
    st.caption("Distribución por buckets")
    pie_options = {
        "color": echarts_colors,
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>Valor: {c} USD<br/>{d}%"},
        "legend": {"show": False},
        "series": [{
            "name": "Buckets",
            "type": "pie",
            "radius": ["40%", "70%"],
            "selectedMode": "single",
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 1},
            "label": {"show": True, "position": "inside", "formatter": "{b}\n{d}%"},
            "labelLine": {"show": False},
            "data": pie_data
        }]
    }
    click_ret = st_echarts(
        options=pie_options,
        height="360px",
        key=f"pie_{filters_version}",
        events={"click": "function(p){ return {name: p.name, value: p.value}; }"}
    )
    clicked_bucket_es = click_ret["name"] if isinstance(click_ret, dict) and "name" in click_ret else None

# ================== APLICAR FILTROS ==================
df_filtered = df.copy()

def apply_eq_filter(frame, column, selected_value):
    if selected_value != "Todos":
        return frame[frame[column].astype(str) == str(selected_value)]
    return frame

for col_f, sel in [
    ("BUKRS_TXT", sel_BUKRS_TXT),
    ("KUNNR_TXT", sel_KUNNR_TXT),
    ("PRCTR", sel_PRCTR),
    ("VKORG_TXT", sel_VKORG_TXT),
    ("VTWEG_TXT", sel_VTWEG_TXT)
]:
    df_filtered = apply_eq_filter(df_filtered, col_f, sel)

if clicked_bucket_es in reverse_label_map:
    col_original = reverse_label_map[clicked_bucket_es]
    if col_original in metric_cols:
        df_filtered = df_filtered[smart_to_numeric(df_filtered[col_original]) > 0]
        st.success(f"Filtrado por sector: {clicked_bucket_es}")

# ================== TRES TABLAS CUADRADAS, MÁS ANCHAS, SIN SCROLL HORIZONTAL ==================
def summarize_in_millions(frame: pd.DataFrame, group_col: str, label: str) -> pd.DataFrame:
    num_cols = [f"_{c}_NUM" for c in metric_cols]
    tmp = frame.copy()
    tmp["_TOTAL_USD_NUM"] = tmp[num_cols].sum(axis=1)
    out = (
        tmp.groupby(group_col, dropna=False)["_TOTAL_USD_NUM"]
           .sum()
           .sort_values(ascending=False)
           .reset_index()
    )
    out.rename(columns={group_col: label}, inplace=True)
    out["M USD"] = (out["_TOTAL_USD_NUM"] / 1_000_000).round(2)
    out = out[[label, "M USD"]]
    # Truncar etiquetas demasiado largas para evitar ancho extra (sin cortar info clave)
    out[label] = out[label].astype(str).str.slice(0, 28)
    return out

with col_tables:
    # Tres columnas internas iguales; al tener más ancho total, cada una queda más ancha.
    t1, t2, t3 = st.columns(3)

    with t1:
        st.markdown('<div class="mini-title">Mercado</div>', unsafe_allow_html=True)
        st.dataframe(
            summarize_in_millions(df_filtered, "VKORG_TXT", "Mercado"),
            use_container_width=True, hide_index=True, height=320
        )

    with t2:
        st.markdown('<div class="mini-title">Canal</div>', unsafe_allow_html=True)
        st.dataframe(
            summarize_in_millions(df_filtered, "VTWEG_TXT", "Canal"),
            use_container_width=True, hide_index=True, height=320
        )

    with t3:
        st.markdown('<div class="mini-title">Cliente</div>', unsafe_allow_html=True)
        st.dataframe(
            summarize_in_millions(df_filtered, "KUNNR_TXT", "Cliente"),
            use_container_width=True, hide_index=True, height=320
        )

# ================== TABLA DETALLE ==================
drop_aux = [f"_{col}_NUM" for c in metric_cols for col in [c]]
st.dataframe(
    df_filtered.drop(columns=drop_aux, errors="ignore"),
    use_container_width=True, hide_index=True
)
