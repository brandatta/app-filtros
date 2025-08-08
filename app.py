import streamlit as st
import pandas as pd

# ---------------- CONFIGURACIÓN BÁSICA ----------------
st.set_page_config(page_title="Visor de Aging con Filtros", layout="wide")
st.title("📄 Visor de Excel con Filtros a la Izquierda")

REQUIRED_COLUMNS = ["BUKRS_TXT", "KUNNR_TXT", "PRCTR", "VKORG_TXT", "VTWEG_TXT", "NOT_DUE_AMOUNT"]

# ---------------- CARGA DE ARCHIVO ----------------
with st.expander("📥 Cargar archivo Excel", expanded=True):
    uploaded_file = st.file_uploader("Subí tu archivo .xlsx", type=["xlsx"])
    st.caption("Formato esperado: Excel con las columnas BUKRS_TXT, KUNNR_TXT, PRCTR, VKORG_TXT, VTWEG_TXT y NOT_DUE_AMOUNT")

@st.cache_data(show_spinner=False)
def load_excel(_file):
    df = pd.read_excel(_file)
    df.columns = [str(c).strip() for c in df.columns]
    return df

df = None
if uploaded_file:
    try:
        df = load_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")

if df is None:
    st.stop()

# ---------------- VALIDACIÓN DE COLUMNAS ----------------
missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas en el Excel: {', '.join(missing)}")
    st.stop()

# ---------------- LAYOUT CON COLUMNA IZQUIERDA ----------------
left, right = st.columns([1, 3], gap="large")

with left:
    st.subheader("🔎 Filtros")
    st.markdown("Seleccioná un valor por filtro. Elegí **Todos** para no aplicar filtro en ese campo.")

    def select_from_column(label, colname):
        uniques = pd.Series(df[colname].dropna().unique())
        try:
            uniques = uniques.sort_values()
        except Exception:
            pass
        options = [None] + uniques.tolist()
        return st.selectbox(label, options=options, format_func=lambda x: "Todos" if x is None else str(x))

    sel_BUKRS_TXT   = select_from_column("BUKRS_TXT",   "BUKRS_TXT")
    sel_KUNNR_TXT   = select_from_column("KUNNR_TXT",   "KUNNR_TXT")
    sel_PRCTR       = select_from_column("PRCTR",       "PRCTR")
    sel_VKORG_TXT   = select_from_column("VKORG_TXT",   "VKORG_TXT")
    sel_VTWEG_TXT   = select_from_column("VTWEG_TXT",   "VTWEG_TXT")
    sel_NOT_DUE_AMT = select_from_column("NOT_DUE_AMOUNT", "NOT_DUE_AMOUNT")

    if st.button("🧹 Limpiar filtros", use_container_width=True):
        st.experimental_rerun()

with right:
    df_filtered = df.copy()
    if sel_BUKRS_TXT is not None:
        df_filtered = df_filtered[df_filtered["BUKRS_TXT"] == sel_BUKRS_TXT]
    if sel_KUNNR_TXT is not None:
        df_filtered = df_filtered[df_filtered["KUNNR_TXT"] == sel_KUNNR_TXT]
    if sel_PRCTR is not None:
        df_filtered = df_filtered[df_filtered["PRCTR"] == sel_PRCTR]
    if sel_VKORG_TXT is not None:
        df_filtered = df_filtered[df_filtered["VKORG_TXT"] == sel_VKORG_TXT]
    if sel_VTWEG_TXT is not None:
        df_filtered = df_filtered[df_filtered["VTWEG_TXT"] == sel_VTWEG_TXT]
    if sel_NOT_DUE_AMT is not None:
        df_filtered = df_filtered[df_filtered["NOT_DUE_AMOUNT"] == sel_NOT_DUE_AMT]

    st.subheader("📊 Tabla filtrada")
    st.caption(f"{len(df_filtered):,} filas coinciden con los filtros seleccionados.")
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    @st.cache_data(show_spinner=False)
    def to_excel_bytes(_df):
        import io
        with pd.ExcelWriter(io.BytesIO(), engine="xlsxwriter") as writer:
            _df.to_excel(writer, index=False, sheet_name="Datos")
            writer.close()
            return writer.book.filename.getvalue()

    col_a, col_b = st.columns(2)
    with col_a:
        csv_data = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar CSV", data=csv_data, file_name="filtrado.csv", mime="text/csv", use_container_width=True)
    with col_b:
        try:
            xlsx_data = to_excel_bytes(df_filtered)
            st.download_button("⬇️ Descargar Excel", data=xlsx_data, file_name="filtrado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception:
            st.warning("No se pudo generar Excel. Probá descargar CSV.")

st.markdown(
    """
    <style>
      .block-container { padding-top: 0.5rem; }
      h1, h2, h3 { line-height: 1.1; }
    </style>
    """,
    unsafe_allow_html=True
)
