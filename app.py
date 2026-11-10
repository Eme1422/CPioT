import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE LA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Tótem IoT - EAFIT",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    return df

try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Error al cargar el archivo de datos: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. FILTROS EN BARRA LATERAL
# -----------------------------------------------------------------------------
st.sidebar.image("https://www.eafit.edu.co/imagen-institucional/logo-eafit.png", width=200) # Opcional
st.sidebar.title("🎛️ Filtros de Control")

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
    # Indicadores Generales (KPIs)
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

    # Visualizaciones
    st.subheader("📈 Visualizaciones Interactivas")
    
    # Fila 1: Evolución Temporal y Calidad
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
        fig_status = px.pie(
            df_status, names="Estado", values="Cantidad",
            title="Distribución de Calidad de Mediciones (Válidas vs Inválidas)",
            color="Estado",
            color_discrete_map={"valid": "#2ecc71", "invalid": "#e74c3c"}
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # Fila 2: Distribuciones de BPM y SpO2 (Solo Válidas)
    c3, c4 = st.columns(2)
    
    with c3:
        fig_bpm = px.histogram(
            df_validas, x="heart_rate_bpm", nbins=30,
            title="Distribución de Frecuencia Cardíaca (BPM) - Registros Válidos",
            labels={"heart_rate_bpm": "BPM"},
            color_discrete_sequence=["#3498db"]
        )
        st.plotly_chart(fig_bpm, use_container_width=True)

    with c4:
        fig_spo2 = px.histogram(
            df_validas, x="spo2_percent", nbins=30,
            title="Distribución de Saturación de Oxígeno (SpO₂) - Registros Válidos",
            labels={"spo2_percent": "SpO₂ (%)"},
            color_discrete_sequence=["#9b59b6"]
        )
        st.plotly_chart(fig_spo2, use_container_width=True)

    # Fila 3: Horarios de Utilización
    st.subheader("⏰ Patrones de Uso")
    df_hora = df_filtered.groupby("hora").size().reset_index(name="conteo")
    fig_hora = px.bar(
        df_hora, x="hora", y="conteo",
        title="Horarios de Mayor Utilización del Tótem (Hora Local Colombia)",
        labels={"hora": "Hora del Día (0-23)", "conteo": "Número de Mediciones"},
        color="conteo", color_continuous_scale="Viridis"
    )
    st.plotly_chart(fig_hora, use_container_width=True)

# =============================================================================
# TAB 2: SEGUIMIENTO INDIVIDUAL
# =============================================================================
with tab2:
    st.subheader("👤 Histórico por Estudiante")
    
    estudiantes_disponibles = sorted(df_raw["student_id"].unique())
    estudiante_sel = st.selectbox("Seleccionar Identificador de Estudiante (Student ID)", estudiantes_disponibles)

    df_est = df_filtered[df_filtered["student_id"] == estudiante_sel].sort_values("timestamp_colombia")

    if df_est.empty:
        st.warning("No se encontraron mediciones para este estudiante en el rango de fechas/filtros seleccionado.")
    else:
        # Métricas individuales
        primera_med = df_est["timestamp_colombia"].min().strftime("%Y-%m-%d %H:%M")
        ultima_med = df_est["timestamp_colombia"].max().strftime("%Y-%m-%d %H:%M")
        cant_med = len(df_est)
        
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("Total Mediciones Registradas", cant_med)
        ic2.metric("Primera Medición", primera_med)
        ic3.metric("Última Medición", ultima_med)

        st.divider()

        # Gráfico evolutivo de BPM y SpO2
        st.markdown("#### Evolución Fisiológica Individual")
        df_est_valid = df_est[df_est["measurement_status"] == "valid"]

        if df_est_valid.empty:
            st.warning("El estudiante seleccionado no tiene registros con estado 'valid' en el período.")
        else:
            fig_indiv = go.Figure()

            # Serie BPM
            fig_indiv.add_trace(go.Scatter(
                x=df_est_valid["timestamp_colombia"], y=df_est_valid["heart_rate_bpm"],
                mode="lines+markers", name="BPM", line=dict(color="#e74c3c")
            ))

            # Serie SpO2
            fig_indiv.add_trace(go.Scatter(
                x=df_est_valid["timestamp_colombia"], y=df_est_valid["spo2_percent"],
                mode="lines+markers", name="SpO₂ (%)", line=dict(color="#2980b9"), yaxis="y2"
            ))

            fig_indiv.update_layout(
                title=f"Evolución Temporal para {estudiante_sel}",
                xaxis=dict(title="Fecha y Hora"),
                yaxis=dict(
    title=dict(
        text="BPM (Pulsaciones por minuto)",
        font=dict(color="#e74c3c")
    ),
    tickfont=dict(color="#e74c3c")
),

yaxis2=dict(
    title=dict(
        text="SpO₂ (%)",
        font=dict(color="#2980b9")
    ),
    tickfont=dict(color="#2980b9"),
    overlaying="y",
    side="right"
),
            )
            st.plotly_chart(fig_indiv, use_container_width=True)

        # Tabla detallada del estudiante
        st.markdown("#### Registro Detallado de Mediciones")
        st.dataframe(df_est[["timestamp_colombia", "heart_rate_bpm", "spo2_percent", "signal_quality", "measurement_status"]], use_container_width=True)

# =============================================================================
# TAB 3: HALLAZGOS Y ANÁLISIS
# =============================================================================
with tab3:
    st.subheader("🔍 Interpretación de Resultados y Hallazgos Relevantes")

    st.markdown("""
    ### 1. Patrones de Utilización y Picos de Horario
    - **Picos de Uso:** Se observa una mayor densidad de interacción con el tótem en horas de cambio de clase y al mediodía (entre las 10:00 AM y 2:00 PM), así como al final de la tarde (4:00 PM a 6:00 PM).
    - **Frecuencia de Uso:** No todos los estudiantes interactúan con la misma periodicidad. Un porcentaje menor de usuarios representa una gran parte del total de mediciones.

    ### 2. Calidad de Señal y Registros Inválidos
    - **Filtro de Estado:** Las mediciones clasificadas como `invalid` coinciden en su mayoría con valores de `signal_quality` bajos (inferiores a 0.5) o artefactos de movimiento producidos durante la lectura del sensor óptico MAX30102.
    - **Valores Atípicos:** En las mediciones válidas existen fluctuaciones normales atribuibles al estado del estudiante antes de realizar la prueba (p. ej. llegar caminando rápido o subir escaleras).

    ### 3. Consideraciones y Limitaciones del Monitoreo IoT
    - **Naturaleza Sintética Educativa:** Los datos expuestos en este dashboard corresponden a un escenario simulado para fines estrictamente académicos en la Universidad EAFIT.
    - **No es un Dispositivo Médico:** El sensor MAX30102 implementado en un prototipo experimental no cuenta con certificación clínica. Por tanto, los valores calculados no constituyen diagnósticos ni evaluación médica formal.
    """)