import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Representantes", layout="wide")

# Carga de datos con caché
@st.cache_data
def load_data():
    # Los datos reales están en las hojas 'repreAAAA', NO en 'Hoja1' ni 'Diputado 3'.
    # 'Hoja1' en los archivos 2014/2024 es solo una hoja auxiliar de pocas filas.
    df_2014 = pd.read_excel(
        "Cuadro_13_-_Representantes_Proclamados_2014_DESBLOQ.xlsx",
        sheet_name="repre2014",
    )
    df_2019 = pd.read_excel(
        "Representantes_Proclamados_2019_DESBLOQ.xlsx",
        sheet_name="repre2019",
    )
    df_2024 = pd.read_excel(
        "Cuadro_13_Representantes_Proclamados_2024_DESBLOQ.xlsx",
        sheet_name="repre2024",
    )

    # Estandarización básica
    # Cada archivo tiene 7 columnas: PROVINCIA, DISTRITO, CORREGIMIENTO,
    # CANDIDATO ELECTO, PARTIDO POLÍTICO, TOTAL DE VOTOS OBTENIDOS, OBSERVACIÓN
    for df, year in [(df_2014, 2014), (df_2019, 2019), (df_2024, 2024)]:
        df["Año"] = year
        # Renombrar columnas para consistencia (7 originales + 'Año' = 8)
        df.columns = [
            "Provincia",
            "Distrito",
            "Corregimiento",
            "Candidato",
            "Partido",
            "Votos",
            "Observacion",
            "Año",
        ]

    df_master = pd.concat([df_2014, df_2019, df_2024], ignore_index=True)

    # La columna de votos viene con tipos distintos entre años
    # (texto en 2014, float en 2019, int en 2024). La forzamos a numérico
    # para que .sum() y los gráficos funcionen correctamente.
    df_master["Votos"] = pd.to_numeric(df_master["Votos"], errors="coerce").fillna(0)

    # Estandarización de partidos
    def clean_party(p):
        p = str(p).upper()
        if "/" in p:
            p = p.split("/")[0].strip()
        if "PANAMEÑISTA" in p or "PP" in p:
            return "PANAMEÑISTA"
        if "LIBRE POSTULACIÓN" in p or "IND" in p:
            return "IND_LP"
        return p

    df_master["Partido"] = df_master["Partido"].apply(clean_party)
    return df_master

df = load_data()

# Título
st.title("EVOLUCIÓN DE LOS PROCESOS ELECTORALES - REPRESENTANTES 2014 - 2019 - 2024")

# Sidebar
st.sidebar.header("Filtros")
years = st.sidebar.multiselect("Año", [2014, 2019, 2024], default=[2014, 2019, 2024])
provincias = st.sidebar.multiselect("Provincia", df["Provincia"].unique())

mask = (df["Año"].isin(years))
if provincias:
    mask &= (df["Provincia"].isin(provincias))
df_filt = df[mask]

# Tabs
tab1, tab2, tab3 = st.tabs(["Métricas Globales", "Balance de Poder", "Detalle por Corregimiento"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Votos", f"{int(df_filt['Votos'].sum()):,}")
    col2.metric("Total Representantes", len(df_filt))
    col3.metric("Partidos Únicos", df_filt["Partido"].nunique())

    fig = px.bar(
        df_filt.groupby("Provincia")["Votos"].sum().reset_index(),
        x="Provincia",
        y="Votos",
        title="Votos por Provincia",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Distribución de Representantes por Partido")
    dist_partido = df_filt.groupby(["Año", "Partido"]).size().reset_index(name="Conteo")
    fig2 = px.bar(
        dist_partido,
        x="Año",
        y="Conteo",
        color="Partido",
        barmode="stack",
        title="Evolución de fuerza política (Cantidad de Corregimientos)",
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Buscador de Resultados")
    search = st.text_input("Buscar por candidato o corregimiento")
    if search:
        df_search = df_filt[
            df_filt["Candidato"].astype(str).str.contains(search, case=False, na=False)
            | df_filt["Corregimiento"].astype(str).str.contains(search, case=False, na=False)
        ]
        st.dataframe(df_search)
    else:
        st.dataframe(df_filt)
