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
    </style>
    """,
    unsafe_allow_html=True
)

# Columnas requeridas
REQUIRED_COLUMNS = ["BUKRS_TXT", "KUNNR_TXT", "PRCTR", "VKORG_TXT", "VTWEG_TXT", "NOT_DUE_AMOUNT"]

# ================== CARGA DE DATOS ==================
@st.cache_data(show_spinner=False)
def load_excel(path_or_buffer):
    df = pd.read_excel(path_or_buffer)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = None
default_path = Path("AGING AL 2025-01-28.xlsx")  # cambia si lo tenés en otra ruta

# Uploader en la barra izquierda (sidebar), similar a la página de referencia
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
        # valores únicos (sin NaN), ordenados
        vals = pd.Series(df[colname].dropna().unique())
        try:
            vals = vals.sort_values()
        except Exception:
            pass
        options = ["Todos"] + vals.astype(str).tolist()

        # recordar selección en session_state sin usar experimental_rerun
        key = f"sel_{colname}"
        if key not in st.session_state:
            st.session_state[key] = "Todos"

        return st.selectbox(label, options=options, index=options.index(st.session_state[key]), key=key)

    sel_BUKRS_TXT   = dropdown("BUKRS_TXT",   "BUKRS_TXT")
    sel_KUNNR_TXT   = dropdown("KUNNR_TXT",   "KUNNR_TXT")
    sel_PRCTR       = dropdown("PRCTR",       "PRCTR")
    sel_VKORG_TXT   = dropdown("VKORG_TXT",   "VKORG_TXT")
    sel_VTWEG_TXT   = dropdown("VTWEG_TXT",   "VTWEG_TXT")
    # Para NOT_DUE_AMOUNT mostramos también como texto para el dropdown
    sel_NOT_DUE_AMT = dropdown("NOT_DUE_AMOUNT", "NOT_DUE_AMOUNT")

# ================== APLICAR FILTROS ==================
df_filtered = df.copy()

def apply_eq_filter(frame, column, selected_value):
    if selected_value != "Todos":
        # Convertimos ambos a str para comparación segura con lo elegido en el dropdown
        return frame[frame[column].astype(str) == str(selected_value)]
    return frame

df_filtered = apply_eq_filter(df_filtered, "Sociedad", sel_BUKRS_TXT)
df_filtered = apply_eq_filter(df_filtered, "Cliente", sel_KUNNR_TXT)
df_filtered = apply_eq_filter(df_filtered, "Cen.Ben", sel_PRCTR)
df_filtered = apply_eq_filter(df_filtered, "Mercado", sel_VKORG_TXT)
df_filtered = apply_eq_filter(df_filtered, "Canal", sel_VTWEG_TXT)

# ================== TABLA ==================
st.dataframe(df_filtered, use_container_width=True, hide_index=True)

# ================== DESCARGAS ==================
col1, col2 = st.columns(2)
with col1:
    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
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
        xlsx_data = to_excel_bytes(df_filtered)
        st.download_button("Descargar Excel", data=xlsx_data, file_name="aging_filtrado.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    except Exception:
        st.warning("No se pudo generar el Excel. Probá con CSV.")
