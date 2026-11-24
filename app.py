import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- Paleta del curso ---
GRIS = "#B9C3D1"
AZUL = "#1C4C9A"
ROJO = "#B2182B"
CUALI = ["#E69F00", "#56B4E9", "#009E73", "#0072B2"]
sns.set_theme(style="whitegrid")

st.set_page_config(page_title="Dashboard TMDB", layout="wide")

# --- 1. Gestión del Token ---
# En local leerá de .streamlit/secrets.toml, en la nube de los Secrets de Streamlit
try:
    TOKEN = st.secrets["tmdb_api_key"]
except Exception:
    st.error("Falta la API Key de TMDB. Revisa los secretos de la app.")
    st.stop()

# --- 2. Consulta a la API (con Caché) ---
@st.cache_data(ttl=3600, show_spinner=False)
def descargar_datos(token, paginas):
    resultados = []
    for pagina in range(1, paginas + 1):
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={token}&language=es-ES&page={pagina}"
        respuesta = requests.get(url)
        if respuesta.status_code == 401:
            raise PermissionError("API Key inválida.")
        respuesta.raise_for_status()
        resultados.extend(respuesta.json()["results"])
    return resultados

# --- 3. Controles en la barra lateral ---
with st.sidebar:
    st.header("Filtros")
    paginas_a_descargar = st.slider("Cantidad de páginas a analizar", 1, 10, 5, 
                                    help="Cada página trae 20 películas.")
    st.caption("Fuente: TMDB API")

# --- 4. Procesamiento de datos ---
with st.spinner("Consultando la API de TMDB..."):
    try:
        datos = descargar_datos(TOKEN, paginas_a_descargar)
    except PermissionError as e:
        st.error(str(e))
        st.stop()

df = pd.DataFrame(datos)
df = df[["title", "release_date", "vote_average", "popularity", "original_language"]].copy()
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["anio"] = df["release_date"].dt.year

# --- 5. Encabezado e Indicadores ---
st.title("Análisis de Películas (TMDB)")
st.markdown(f"Analizando las **{len(df)}** películas más populares de la muestra actual.")

c1, c2, c3 = st.columns(3)
c1.metric("Puntuación Promedio", f"{df['vote_average'].mean():.1f} / 10")
c2.metric("Película más popular", df.loc[df['popularity'].idxmax(), 'title'][:30] + "...")
c3.metric("Películas sin calificación", (df["vote_average"] == 0).sum())

st.divider()

# --- 6. Las Gráficas ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribución de Puntuaciones")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(data=df[df["vote_average"] > 0], x="vote_average", bins=20, color=AZUL, ax=ax)
    ax.set_xlabel("Puntuación (0-10)")
    ax.set_ylabel("Cantidad de películas")
    st.pyplot(fig)

with col2:
    st.subheader("Idiomas más populares")
    fig, ax = plt.subplots(figsize=(6, 4))
    # Filtramos solo los 5 idiomas más comunes para no saturar
    top_idiomas = df["original_language"].value_counts().head(5).index
    df_top = df[df["original_language"].isin(top_idiomas)]
    sns.countplot(data=df_top, y="original_language", order=top_idiomas, palette=CUALI, ax=ax)
    ax.set_xlabel("Cantidad de películas")
    ax.set_ylabel("Idioma original")
    st.pyplot(fig)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Popularidad vs. Puntuación")
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.scatterplot(data=df, x="popularity", y="vote_average", color=AZUL, alpha=0.6, ax=ax)
    ax.set_xlabel("Índice de Popularidad")
    ax.set_ylabel("Puntuación")
    st.pyplot(fig)

with col4:
    st.subheader("Estrenos por Año (Últimos 20 años)")
    fig, ax = plt.subplots(figsize=(6, 4))
    # Filtramos años válidos
    df_anios = df[df["anio"] >= 2004]
    sns.histplot(data=df_anios, x="anio", bins=20, kde=True, color=AZUL, ax=ax)
    ax.set_xlabel("Año de estreno")
    ax.set_ylabel("Cantidad de películas")
    st.pyplot(fig)

st.divider()
st.caption("Dashboard generado para la Práctica de Visualización de Datos.")