import streamlit as st
import pandas as pd
from pathlib import Path

# ================== CONFIG ==================
st.set_page_config(page_title="Aging - Filtros", layout="wide")

# Ocultar cabecera, menú y footer de Streamlit
st.markdown(
    """
    <style>
      header {visibility: hidden;}
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      .block-container { padding-top: 0.5rem; }
      /* Tarjetas métricas */
      .metric-card {
          border-radius: 16px;
          padding: 14px 18px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.06);
          border: 1px solid rgba(0,0,0,0.06);
          display: inline-block;
          margin: 0 10px 10px 0;
          min-width: 150px;
          vertical-align: top;
      }
      .metric-label {
          font-size: 12px;
          opacity: 0.8;
          margin-bottom: 4px;
      }
      .metric-value {
          font-size: 22px;
          font-weight: 700;
          line-height: 1.1;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# Columnas requeridas para filtros y métricas
REQUIRED_COLUMNS = [
    "BUKRS_TXT", "KUNNR_TXT", "PRCTR", "VKORG_TXT", "VTWEG_TXT",
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
default_path = Path("AGING AL 2025-01-28.xlsx")  # poné el archivo en la misma carpeta si querés carga automática

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
        key = f"sel_{colname}"
        if key not in st.session_state:
            st.session_state[key] = "Todos"
        return st.selectbox(label, options=options, index=options.index(st.session_state[key]), key=key)

    sel_BUKRS_TXT = dropdown("Sociedad", "BUKRS_TXT")
    sel_KUNNR_TXT = dropdown("Cliente", "KUNNR_TXT")
    sel_PRCTR     = dropdown("Cen.Ben",  "PRCTR")
    sel_VKORG_TXT = dropdown("Mercado",  "VKORG_TXT")
    sel_VTWEG_TXT = dropdown("Canal",    "VTWEG_TXT")

    # Botón para limpiar filtros
    if st.button("Limpiar filtros", use_container_width=True):
        st.session_state["sel_BUKRS_TXT"] = "Todos"
        st.session_state["sel_KUNNR_TXT"] = "Todos"
        st.session_state["sel_PRCTR"]     = "Todos"
        st.session_state["sel_VKORG_TXT"] = "Todos"
        st.session_state["sel_VTWEG_TXT"] = "Todos"

# ================== CALCULAR Y MOSTRAR TARJETAS ==================
metric_cols = [
    "NOT_DUE_AMOUNT_USD", "DUE_30_DAYS_USD", "DUE_60_DAYS_USD", "DUE_90_DAYS_USD",
    "DUE_120_DAYS_USD", "DUE_180_DAYS_USD", "DUE_270_DAYS_USD", "DUE_360_DAYS_USD", "DUE_OVER_360_DAYS_USD"
]

# Asegurar columnas numéricas (por si vienen como texto)
for col in metric_cols:
    df[f"_{col}_NUM"] = pd.to_numeric(df[col], errors="coerce").fillna(0)

def format_usd(x: float) -> str:
    return f"US$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Base para tarjetas: si hay Cliente seleccionado, suma por ese cliente; si no, suma total
if sel_KUNNR_TXT != "Todos":
    df_for_metrics = df[df["KUNNR_TXT"].astype(str) == str(sel_KUNNR_TXT)]
else:
    df_for_metrics = df

cards_html = ""
for col in metric_cols:
    val = df_for_metrics[f"_{col}_NUM"].sum()
    cards_html += f"""
    <div class="metric-card">
        <div class="metric-label">{col}</div>
        <div class="metric-value">{format_usd(val)}</div>
    </div>
    """
st.markdown(cards_html, unsafe_allow_html=True)

# ================== APLICAR FILTROS A LA TABLA ==================
df_filtered = df.copy()

def apply_eq_filter(frame, column, selected_value):
    if selected_value != "Todos":
        return frame[frame[column].astype(str) == str(selected_value)]
    return frame

df_filtered = apply_eq_filter(df_filtered, "BUKRS_TXT", sel_BUKRS_TXT)
df_filtered = apply_eq_filter(df_filtered, "KUNNR_TXT", sel_KUNNR_TXT)
df_filtered = apply_eq_filter(df_filtered, "PRCTR",     sel_PRCTR)
df_filtered = apply_eq_filter(df_filtered, "VKORG_TXT", sel_VKORG_TXT)
df_filtered = apply_eq_filter(df_filtered, "VTWEG_TXT", sel_VTWEG_TXT)

# ================== TABLA ==================
drop_aux = [f"_{col}_NUM" for col in metric_cols]
st.dataframe(df_filtered.drop(columns=drop_aux, errors="ignore"),
             use_container_width=True, hide_index=True)

# ================== DESCARGAS ==================
col1, col2 = st.columns(2)
with col1:
    csv_data = df_filtered.drop(columns=drop_aux, errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV", data=csv_data, file_name="aging_filtrado.csv", mime="text/csv", use_container_width=True)
with col2:
    @st.cache_data(show_spinner=False)
    def to_excel_bytes(_df):
        import io
        with pd.ExcelWriter(io.BytesIO(), engine="xlsxwriter") as writer:
            _df.to_excel(writer, index=False, sheet_name="Datos")
            writer.close()
            return writer.book.filename.getvalue()
    try:
        xlsx_data = to_excel_bytes(df_filtered.drop(columns=drop_aux, errors="ignore"))
        st.download_button(
            "Descargar Excel",
            data=xlsx_data,
            file_name="aging_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception:
        st.warning("No se pudo generar el Excel. Probá con CSV.")
