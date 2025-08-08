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
    if st.button("🧹 Limpiar filtros", use_container_width=True):
        st.session_state.sel_BUKRS_TXT = "Todos"
        st.session_state.sel_KUNNR_TXT = "Todos"
        st.session_state.sel_PRCTR     = "Todos"
        st.session_state.sel_VKORG_TXT = "Todos"
        st.session_state.sel_VTWEG_TXT = "Todos"

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
