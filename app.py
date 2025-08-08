import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from streamlit_echarts import st_echarts

# ================== CONFIG ==================
st.set_page_config(page_title="Aging - Filtros", layout="wide")

# Convertir logo a base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logorelleno (1).png")

# Contenedor título + logo
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: center; position: relative; margin-bottom: 0.75rem;">
        <h1 style="font-size:1.5rem; margin:0;">Draft Biosidus Aging</h1>
        <img src="data:image/png;base64,{logo_base64}" alt="Logo"
             style="height:50px; position: absolute; right: -20px; top: 8px;">
    </div>
    """,
    unsafe_allow_html=True
)

# ============= Estilos extra para tablas y métricas =============
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

      /* Mini tablas */
      .mini-title { font-weight: 600; margin: 0 0 6px 2px; }
      .table-box { height: 320px; overflow-y: auto; overflow-x: hidden; }
      .table-compact { width: 100%; table-layout: fixed; border-collapse: collapse; }
      .table-compact th, .table-compact td {
          padding: 6px 8px; border-bottom: 1px solid #eee; font-size: 12px; vertical-align: top;
      }
      .table-compact th { position: sticky; top: 0; background: #fafafa; z-index: 1; }
      .table-compact th:first-child, .table-compact td:first-child { width: 68%; }
      .table-compact th:last-child, .table-compact td:last-child { width: 32%; text-align: right; }
      .table-compact td { word-break: break-word; white-space: normal; }
    </style>
    """,
    unsafe_allow_html=True
)

# ================== COLUMNAS ==================
REQUIRED_COLUMNS = [
    "BUKRS_TXT", "KUNNR_TXT", "PRCTR", "VKORG_TXT", "VTWEG_TXT",
    "NOT_DUE_AMOUNT_USD", "DUE_30_DAYS_USD", "DUE_60_DAYS_USD", "DUE_90_DAYS_USD",
    "DUE_120_DAYS_USD", "DUE_180_DAYS_USD", "DUE_270_DAYS_USD", "DUE_360_DAYS_USD", "DUE_OVER_360_DAYS_USD"
]
metric_cols = REQUIRED_COLUMNS[5:]

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
        df = load_excel(up)

if df is None and default_path.exists():
    df = load_excel(default_path)

if df is None:
    st.info("Cargá un archivo Excel (xlsx) desde la barra izquierda.")
    st.stop()

# Validar columnas
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas: {', '.join(missing)}")
    st.stop()

# ================== NUMÉRICOS ==================
def smart_to_numeric(s: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(s):
        return s.fillna(0)
    s1 = pd.to_numeric(s, errors="coerce")
    return s1.fillna(0)

for col in metric_cols:
    df[f"_{col}_NUM"] = smart_to_numeric(df[col])

# ================== FILTROS ==================
if "filters_version" not in st.session_state:
    st.session_state["filters_version"] = 0
filters_version = st.session_state["filters_version"]

with st.sidebar:
    st.markdown("**Filtros**")
    def dropdown(label, colname):
        vals = sorted(df[colname].dropna().unique())
        options = ["Todos"] + [str(v) for v in vals]
        return st.selectbox(label, options=options, index=0, key=f"{colname}_{filters_version}")
    sel_BUKRS_TXT = dropdown("Sociedad", "BUKRS_TXT")
    sel_KUNNR_TXT = dropdown("Cliente", "KUNNR_TXT")
    sel_PRCTR     = dropdown("Cen.Ben", "PRCTR")
    sel_VKORG_TXT = dropdown("Mercado", "VKORG_TXT")
    sel_VTWEG_TXT = dropdown("Canal", "VTWEG_TXT")
    if st.button("🧹 Limpiar filtros", use_container_width=True):
        st.session_state["filters_version"] += 1

# ================== TARJETAS ==================
df_for_metrics = df if sel_KUNNR_TXT == "Todos" else df[df["KUNNR_TXT"] == sel_KUNNR_TXT]
def format_usd_millions(x: float) -> str:
    return f"US$ {x/1_000_000:,.2f}M".replace(",", "X").replace(".", ",").replace("X", ".")
cards_html = "".join(
    f"<div class='metric-card'><div class='metric-label'>{col}</div><div class='metric-value'>{format_usd_millions(df_for_metrics[f'_{col}_NUM'].sum())}</div></div>"
    for col in metric_cols
)
st.markdown(cards_html, unsafe_allow_html=True)

# ================== PIE CHART ==================
label_map = {
    "NOT_DUE_AMOUNT_USD": "No vencido", "DUE_30_DAYS_USD": "30", "DUE_60_DAYS_USD": "60",
    "DUE_90_DAYS_USD": "90", "DUE_120_DAYS_USD": "120", "DUE_180_DAYS_USD": "180",
    "DUE_270_DAYS_USD": "270", "DUE_360_DAYS_USD": "360", "DUE_OVER_360_DAYS_USD": "+360"
}
reverse_label_map = {v: k for k, v in label_map.items()}
col_sums = {col: float(df_for_metrics[f"_{col}_NUM"].sum()) for col in metric_cols}
pie_data = [{"name": label_map[k], "value": v} for k, v in col_sums.items() if v > 0]
colors = ["#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE", "#3BA272", "#FC8452", "#9A60B4", "#EA7CCC"]

col_chart, col_tables = st.columns([3, 2.2])
with col_chart:
    st.caption("Distribución por buckets")
    pie_options = {
        "color": colors, "tooltip": {"trigger": "item", "formatter": "{b}<br/>Valor: {c} USD<br/>{d}%"},
        "legend": {"show": False},
        "series": [{"type": "pie", "radius": ["40%", "70%"], "label": {"show": True, "position": "inside", "formatter": "{b}\n{d}%"},
                    "data": pie_data}]
    }
    click_ret = st_echarts(options=pie_options, height="360px",
                           key=f"pie_{filters_version}",
                           events={"click": "function(p){ return {name: p.name}; }"})
    clicked_bucket_es = click_ret["name"] if isinstance(click_ret, dict) and "name" in click_ret else None

# ================== FILTRO CLICK PIE ==================
df_filtered = df.copy()
for col_f, sel in [("BUKRS_TXT", sel_BUKRS_TXT), ("KUNNR_TXT", sel_KUNNR_TXT),
                   ("PRCTR", sel_PRCTR), ("VKORG_TXT", sel_VKORG_TXT), ("VTWEG_TXT", sel_VTWEG_TXT)]:
    if sel != "Todos":
        df_filtered = df_filtered[df_filtered[col_f] == sel]
if clicked_bucket_es in reverse_label_map:
    col_original = reverse_label_map[clicked_bucket_es]
    df_filtered = df_filtered[df_filtered[col_original] > 0]

# ================== TABLAS ==================
def summarize_in_millions(frame: pd.DataFrame, group_col: str, label: str):
    num_cols = [f"_{c}_NUM" for c in metric_cols]
    tmp = frame.copy()
    tmp["_TOTAL"] = tmp[num_cols].sum(axis=1)
    out = tmp.groupby(group_col)["_TOTAL"].sum().reset_index()
    out[label] = out[group_col]
    out["M USD"] = (out["_TOTAL"] / 1_000_000).round(2)
    return out[[label, "M USD"]]

def render_table_html(df_small: pd.DataFrame):
    html = ['<div class="table-box"><table class="table-compact">']
    html.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in df_small.columns) + "</tr></thead><tbody>")
    for _, row in df_small.iterrows():
        html.append(f"<tr><td>{row.iloc[0]}</td><td>{row.iloc[1]:,.2f}</td></tr>")
    html.append("</tbody></table></div>")
    return "".join(html)

with col_tables:
    t1, t2, t3 = st.columns(3)
    t1.markdown("<div class='mini-title'>Mercado</div>", unsafe_allow_html=True)
    t1.markdown(render_table_html(summarize_in_millions(df_filtered, "VKORG_TXT", "Mercado")), unsafe_allow_html=True)
    t2.markdown("<div class='mini-title'>Canal</div>", unsafe_allow_html=True)
    t2.markdown(render_table_html(summarize_in_millions(df_filtered, "VTWEG_TXT", "Canal")), unsafe_allow_html=True)
    t3.markdown("<div class='mini-title'>Cliente</div>", unsafe_allow_html=True)
    t3.markdown(render_table_html(summarize_in_millions(df_filtered, "KUNNR_TXT", "Cliente")), unsafe_allow_html=True)

# ================== DETALLE ==================
drop_aux = [f"_{col}_NUM" for col in metric_cols]
st.dataframe(df_filtered.drop(columns=drop_aux), use_container_width=True, hide_index=True)
