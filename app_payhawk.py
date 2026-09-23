import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import glob

# Configuración de página corporativa
st.set_page_config(page_title="Control Financiero - Payhawk", page_icon="📊", layout="wide")

# Paleta de colores corporativa (Tonos Azules profesionales)
COLOR_PRIMARY = "#1f77b4"
COLOR_SECONDARY = "#aec7e8"
COLOR_ACCENT = "#002b49"

@st.cache_data
def cargar_y_procesar_datos():
    # Búsqueda robusta del archivo Excel dentro de la carpeta 'Datos'
    ruta_carpeta = "Datos"
    archivos = glob.glob(os.path.join(ruta_carpeta, "*.xlsx")) + glob.glob(os.path.join(ruta_carpeta, "*.xls"))
    
    if not archivos:
        return pd.DataFrame()
        
    df = pd.read_excel(archivos[0], sheet_name='Expenses')
    
    # Mapeo y selección estricta de columnas clave
    columnas_map = {
        'Document Date': 'Fecha', 
        'Expense Owner': 'Empleado', 
        'Expense Category': 'Categoria',
        'Total Amount (EUR)': 'Importe_EUR', 
        'Approval Status': 'Estado_Aprobacion', 
        'File 1': 'File 1', 
        'File 2': 'File 2'
    }
    
    df = df[[col for col in columnas_map.keys() if col in df.columns]].rename(columns=columnas_map)
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Columnas calculadas (ETL en Python)
    df['Mes'] = df['Fecha'].dt.strftime('%m - %b')
    df['Alerta_Antiguedad'] = np.where(
        (df['Estado_Aprobacion'] != 'Approved') & ((pd.Timestamp.today() - df['Fecha']).dt.days > 15), 
        'ALERTA', 'OK'
    )
    df['Control_Factura'] = np.where(df['File 1'].notna() | df['File 2'].notna(), 'Con Factura', 'Sin Factura')
    
    # Regla de Auditoría de Duplicados
    df['Duplicado_Fraude'] = df.duplicated(subset=['Fecha', 'Empleado', 'Importe_EUR'], keep=False)
    
    return df

df = cargar_y_procesar_datos()

if df.empty:
    st.error("⚠️ No se encontró ningún archivo Excel de Payhawk en la carpeta 'Datos'. Asegúrate de subirlo al repositorio.")
    st.stop()

# ==========================================
# INTERACTIVIDAD (SLICERS EN BARRA LATERAL)
# ==========================================
st.sidebar.header("Filtros del Modelo")
mes_filtro = st.sidebar.multiselect("Mes", options=sorted(df['Mes'].unique()), default=df['Mes'].unique())
empleado_filtro = st.sidebar.multiselect("Empleado", options=df['Empleado'].unique())
factura_filtro = st.sidebar.multiselect("Control Factura", options=df['Control_Factura'].unique(), default=df['Control_Factura'].unique())

# Filtrado dinámico
df_filtrado = df[df['Mes'].isin(mes_filtro) & df['Control_Factura'].isin(factura_filtro)]
if empleado_filtro:
    df_filtrado = df_filtrado[df_filtrado['Empleado'].isin(empleado_filtro)]

# ==========================================
# BUSINESS VISUALIZATION (KPIs EJECUTIVOS)
# ==========================================
st.title("📊 Dashboard Financiero Payhawk - ACK3")
st.markdown("---")

gasto_total = df_filtrado['Importe_EUR'].sum()
gasto_aprobado = df_filtrado[df_filtrado['Estado_Aprobacion'] == 'Approved']['Importe_EUR'].sum()
gasto_no_aprobado = gasto_total - gasto_aprobado
pct_aprobacion = (gasto_aprobado / gasto_total) * 100 if gasto_total > 0 else 0

# Nuevos KPIs de control documental (Facturas vs Sin Factura)
total_facturas = len(df_filtrado[df_filtrado['Control_Factura'] == 'Con Factura'])
total_sin_factura = len(df_filtrado[df_filtrado['Control_Factura'] == 'Sin Factura'])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Gasto Total (EUR)", f"€ {gasto_total:,.2f}")
col2.metric("Total No Aprobado (EUR)", f"€ {gasto_no_aprobado:,.2f}")
col3.metric("% Aprobación Global", f"{pct_aprobacion:.1f} %")
col4.metric("Control Documental", f"{total_facturas} Con Fact.", f"{total_sin_factura} Sin Fact.", delta_color="inverse")

st.markdown("---")

# ==========================================
# GRÁFICOS ANALÍTICOS (Plotly en tonos azules)
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Gasto por Categoría (Volumen)")
    resumen_cat = df_filtrado.groupby('Categoria')['Importe_EUR'].sum().reset_index().sort_values('Importe_EUR', ascending=True)
    fig_vol = px.bar(
        resumen_cat, x='Importe_EUR', y='Categoria', orientation='h', 
        title='Evolución por Partida Presupuestaria',
        color_discrete_sequence=[COLOR_PRIMARY]
    )
    st.plotly_chart(fig_vol, use_container_width=True)

with col_graf2:
    st.subheader("Cumplimiento Normativo (Proporción)")
    resumen_estado = df_filtrado.groupby(['Categoria', 'Estado_Aprobacion'])['Importe_EUR'].sum().reset_index()
    fig_estado = px.bar(
        resumen_estado, x='Categoria', y='Importe_EUR', color='Estado_Aprobacion', 
        title='Aprobado vs No Aprobado por Categoría', 
        barmode='stack',
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    st.plotly_chart(fig_estado, use_container_width=True)

# ==========================================
# AUDITORÍA FINANCIERA (CONTROL DE DUPLICADOS)
# ==========================================
st.markdown("---")
st.subheader("Auditoría Financiera: Riesgo de Fraude (Duplicados)")
df_fraude = df_filtrado[df_filtrado['Duplicado_Fraude'] == True]

if not df_fraude.empty:
    st.error(f"⚠️ Se han detectado {len(df_fraude)} registros con misma Fecha, Empleado e Importe exacto.")
    st.dataframe(df_fraude[['Fecha', 'Empleado', 'Categoria', 'Importe_EUR', 'Estado_Aprobacion']], use_container_width=True)
else:
    st.success("✅ No se han detectado pagos duplicados en la selección actual.")