import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILOS EN FONDO/CONTENEDORES AZULES
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Tótem IoT - EAFIT",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para aplicar tonos azules sutiles en fondos y contenedores
st.markdown("""
    <style>
    /* Fondo general de la barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #f4f8fc;
    }
    /* Estilo para contenedores de métricas */
    div[data-testid="metric-container"] {
        background-color: #ebf3fc;
        border: 1px solid #d0e1fd;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    /* Títulos principales */
    h1, h2, h3 {
        color: #003366 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CARGA Y PREPROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("proyecto_integrador_eafit_max30102.csv")
    
    # Convertir a datetime en UTC y luego a zona horaria de Colombia
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["timestamp_colombia"] = df["timestamp"].dt.tz_convert("America/Bogota")
    
    # Extraer variables temporales
    df["fecha"] = df["timestamp_colombia"].dt.date
    df["hora"] = df["timestamp_colombia"].dt.hour
    df["dia_semana"] = df["timestamp_colombia"].dt.day_name()
    
    # Función para formatear hora en AM/PM
    def format_hour(h):
        if h == 0:
            return "12 AM"
        elif h < 12:
            return f"{h} AM"
        elif h == 12:
            return "12 PM"
        else:
            return f"{h - 12} PM"
            
    df["hora_am_pm"] = df["hora"].apply(format_hour)
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. BARRA LATERAL: IMAGEN GRANDE PRIMERO Y FILTROS DEBAJO
# -----------------------------------------------------------------------------

# Imagen del osito grande sin subtítulo de texto
try:
    st.sidebar.image("Osito médico de EAFIT.png", use_container_width=True)
except Exception:
    st.sidebar.markdown("""
        <div style="background-color: #dbeafe; padding: 30px; border-radius: 12px; text-align: center; border: 2px dashed #93c5fd; margin-bottom: 15px;">
            <span style="font-size: 55px;">🧸🩺</span><br>
            <b style="color: #1e3a8a; font-size: 16px;">Tótem IoT - EAFIT</b>
        </div>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")

# Título de filtros ubicado debajo de la imagen
st.sidebar.markdown("### 🎛️ Filtros de Control")

# Filtro por rango de fechas
min_fecha = df_raw["fecha"].min()
max_fecha = df_raw["fecha"].max()

fecha_inicio, fecha_fin = st.sidebar.date_input(
    "Seleccionar Rango de Fechas",
    value=(min_fecha, max_fecha),
    min_value=min_fecha,
    max_value=max_fecha
)

# Filtro por Estado de Medición
estados = ["Todos"] + list(df_raw["measurement_status"].unique())
estado_sel = st.sidebar.selectbox("Estado de la Medición", estados)

# Aplicación de Filtros Globales
df_filtered = df_raw.copy()
df_filtered = df_filtered[(df_filtered["fecha"] >= fecha_inicio) & (df_filtered["fecha"] <= fecha_fin)]

if estado_sel != "Todos":
    df_filtered = df_filtered[df_filtered["measurement_status"] == estado_sel]

# -----------------------------------------------------------------------------
# 4. ENCABEZADO PRINCIPAL
# -----------------------------------------------------------------------------
st.title("🩺 Monitoreo Fisiológico - Tótem IoT EAFIT")
st.markdown("""
Esta aplicación permite analizar los datos simulados de frecuencia cardíaca (BPM) y saturación de oxígeno ($SpO_2$) 
recolectados por el tótem interactivo IoT ubicado en el campus de la Universidad EAFIT.
""")
st.divider()

# -----------------------------------------------------------------------------
# 5. PESTAÑAS PRINCIPALES DEL DASHBOARD
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Vista General y KPIs", "👤 Seguimiento Individual", "🔍 Hallazgos y Análisis"])

# =============================================================================
# TAB 1: VISTA GENERAL Y KPIS
# =============================================================================
with tab1:
    st.subheader("📌 Indicadores Clave")
    
    total_mediciones = len(df_filtered)
    total_estudiantes = df_filtered["student_id"].nunique()
    
    df_validas = df_filtered[df_filtered["measurement_status"] == "valid"]
    bpm_prom = df_validas["heart_rate_bpm"].mean() if not df_validas.empty else 0
    spo2_prom = df_validas["spo2_percent"].mean() if not df_validas.empty else 0
    
    invalidas_cnt = len(df_filtered[df_filtered["measurement_status"] == "invalid"])
    pct_invalidas = (invalidas_cnt / total_mediciones * 100) if total_mediciones > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Mediciones", f"{total_mediciones:,}")
    col2.metric("Estudiantes Únicos", f"{total_estudiantes:,}")
    col3.metric("BPM Promedio (Válidos)", f"{bpm_prom:.1f} bpm")
    col4.metric("SpO₂ Promedio (Válidos)", f"{spo2_prom:.1f}%")
    col5.metric("Mediciones Inválidas", f"{invalidas_cnt}", f"{pct_invalidas:.1f}%")

    st.divider()

    st.subheader("📈 Visualizaciones Interactivas")
    
    c1, c2 = st.columns(2)
    
    with c1:
        df_daily = df_filtered.groupby("fecha").size().reset_index(name="conteo")
        fig_daily = px.line(
            df_daily, x="fecha", y="conteo", 
            title="Evolución del Número de Mediciones por Día",
            labels={"fecha": "Fecha", "conteo": "Cantidad de Mediciones"},
            markers=True
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with c2:
        df_status = df_filtered["measurement_status"].value_counts().reset_index()
        df_status.columns = ["Estado", "Cantidad"]
        # Colores personalizados: verde claro y rojo oscuro según la referencia proporcionada
        fig_status = px.pie(
            df_status, names="Estado", values="Cantidad",
            title="Distribución de Calidad de Mediciones (Válidas vs Inválidas)",
            color="Estado",
