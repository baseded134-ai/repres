import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(page_title="Dashboard Representantes", layout="wide")

# Carga de datos con caché
@st.cache_data
def load_data():
    # Usamos read_excel en lugar de read_csv
    # Si la hoja no se llama 'Hoja1', cambia el sheet_name
    df_2014 = pd.read_excel("Nombre_Archivo_2014.xlsx", sheet_name='Hoja1')
    df_2019 = pd.read_excel("Nombre_Archivo_2019.xlsx", sheet_name='Diputado 3') # Ajustar según tu archivo
    df_2024 = pd.read_excel("Nombre_Archivo_2024.xlsx", sheet_name='Diputado 3') # Ajustar según tu archivo

    # Estandarización básica
    for df, year in [(df_2014, 2014), (df_2019, 2019), (df_2024, 2024)]:
        df['Año'] = year
        # Renombrar columnas para consistencia
        df.columns = ['Provincia', 'Distrito', 'Corregimiento', 'Candidato', 'Partido', 'Votos', 'Observacion', 'Año']
    
    df_master = pd.concat([df_2014, df_2019, df_2024], ignore_index=True)
    
    # Estandarización de partidos
    def clean_party(p):
        p = str(p).upper()
        if '/' in p: p = p.split('/')[0].strip()
        if 'PANAMEÑISTA' in p or 'PP' in p: return 'PANAMEÑISTA'
        if 'LIBRE POSTULACIÓN' in p or 'IND' in p: return 'IND_LP'
        return p

    df_master['Partido'] = df_master['Partido'].apply(clean_party)
    return df_master

df = load_data()

# Título
st.title("EVOLUCIÓN DE LOS PROCESOS ELECTORALES - REPRESENTANTES 2014 - 2019 - 2024")

# Sidebar
st.sidebar.header("Filtros")
years = st.sidebar.multiselect("Año", [2014, 2019, 2024], default=[2014, 2019, 2024])
provincias = st.sidebar.multiselect("Provincia", df['Provincia'].unique())

mask = (df['Año'].isin(years))
if provincias: mask &= (df['Provincia'].isin(provincias))
df_filt = df[mask]

# Tabs
tab1, tab2, tab3 = st.tabs(["Métricas Globales", "Balance de Poder", "Detalle por Corregimiento"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Votos", f"{df_filt['Votos'].sum():,}")
    col2.metric("Total Representantes", len(df_filt))
    col3.metric("Partidos Únicos", df_filt['Partido'].nunique())
    
    fig = px.bar(df_filt.groupby('Provincia')['Votos'].sum().reset_index(), 
                 x='Provincia', y='Votos', title="Votos por Provincia")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Distribución de Representantes por Partido")
    dist_partido = df_filt.groupby(['Año', 'Partido']).size().reset_index(name='Conteo')
    fig2 = px.bar(dist_partido, x='Año', y='Conteo', color='Partido', barmode='stack',
                  title="Evolución de fuerza política (Cantidad de Corregimientos)")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Buscador de Resultados")
    search = st.text_input("Buscar por candidato o corregimiento")
    if search:
        df_search = df_filt[df_filt['Candidato'].str.contains(search, case=False) | 
                            df_filt['Corregimiento'].str.contains(search, case=False)]
        st.dataframe(df_search)
    else:
        st.dataframe(df_filt)
