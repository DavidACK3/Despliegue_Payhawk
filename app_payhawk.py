import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import glob
from datetime import datetime

# Configuración de página corporativa
st.set_page_config(page_title="Control Financiero - Payhawk", page_icon="📊", layout="wide")

# Paleta corporativa (Tonos Azules)
COLOR_PRIMARY = "#002244" 
COLOR_SECONDARY = "#005b9f"
COLOR_ACCENT = "#80bfff"

@st.cache_data
def cargar_y_procesar_datos(archivo_ruta):
    df = pd.read_excel(archivo_ruta, sheet_name='Expenses')
    
    # 1. ETL Y RENOMBRADO
    columnas_map = {
        'Document Date': 'Fecha', 'Expense Owner': 'Empleado', 'Expense Category': 'Categoria',
        'Total Amount (EUR)': 'Importe_EUR', 'Approval Status': 'Estado_Aprobacion', 
        'Document Type': 'Tiene_Factura', 'File 1': 'File 1', 'File 2': 'File 2'
    }
    df = df[[col for col in columnas_map.keys() if col in df.columns]].rename(columns=columnas_map)
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # 2. COLUMNAS CALCULADAS
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Fecha'].dt.strftime('%m - ') + df['Fecha'].dt.month.map(meses_es).str[:3].str.capitalize()
    
    df['Alerta_Antiguedad'] = np.where((df['Estado_Aprobacion'] != 'Approved') & ((pd.Timestamp.today() - df['Fecha']).dt.days > 15), 'ALERTA', 'OK')
    df['Control_Factura'] = np.where(df['File 1'].notna() | df['File 2'].notna(), 'Con Factura', 'Sin Factura')
    
    # 3. CONTROL DE DUPLICADOS
    df['Duplicado_Fraude'] = df.duplicated(subset=['Fecha', 'Empleado', 'Importe_EUR'], keep=False)
    
    return df

# Búsqueda dinámica de archivos en la carpeta de despliegue
ruta_carpeta = "Datos"
archivos = glob.glob(os.path.join(ruta_carpeta, "*.xlsx")) + glob.glob(os.path.join(ruta_carpeta, "*.xls"))

if not archivos:
    st.error("⚠️ Carpeta 'Datos' vacía. Sube el Excel de Payhawk al repositorio de GitHub.")
    st.stop()

df = cargar_y_procesar_datos(archivos[0])

# ==========================================
# DASHBOARD EJECUTIVO E INTERACTIVIDAD
# ==========================================
st.sidebar.header("Filtros del Modelo")
mes_filtro = st.sidebar.multiselect("Mes", options=sorted(df['Mes'].unique()), default=sorted(df['Mes'].unique()))
empleado_filtro = st.sidebar.multiselect("Empleado", options=sorted(df['Empleado'].dropna().unique()))
factura_filtro = st.sidebar.multiselect("Control Factura", options=df['Control_Factura'].unique(), default=df['Control_Factura'].unique())

df_filtrado = df[df['Mes'].isin(mes_filtro) & df['Control_Factura'].isin(factura_filtro)]
if empleado_filtro:
    df_filtrado = df_filtrado[df_filtrado['Empleado'].isin(empleado_filtro)]

st.title("📊 Dashboard Financiero Payhawk - ACK3 Global Solutions")

# KPIs
gasto_total = df_filtrado['Importe_EUR'].sum()
gasto_aprobado = df_filtrado[df_filtrado['Estado_Aprobacion'] == 'Approved']['Importe_EUR'].sum()
gasto_no_aprobado = gasto_total - gasto_aprobado
pct_aprobacion = (gasto_aprobado / gasto_total) * 100 if gasto_total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Gasto Total (EUR)", f"€ {gasto_total:,.2f}")
col2.metric("Total No Aprobado (EUR)", f"€ {gasto_no_aprobado:,.2f}")
col3.metric("% Aprobación Global", f"{pct_aprobacion:.1f} %")
st.markdown("---")

# GRÁFICOS
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    resumen_cat = df_filtrado.groupby('Categoria')['Importe_EUR'].sum().reset_index().sort_values('Importe_EUR', ascending=True)
    fig_vol = px.bar(resumen_cat, x='Importe_EUR', y='Categoria', orientation='h', title='Gasto por Categoría (Volumen EUR)', color_discrete_sequence=[COLOR_SECONDARY])
    st.plotly_chart(fig_vol, use_container_width=True)

with col_graf2:
    resumen_estado = df_filtrado.groupby(['Categoria', 'Estado_Aprobacion'])['Importe_EUR'].sum().reset_index()
    mapa_colores = {'Approved': COLOR_PRIMARY, 'Waiting approval': COLOR_SECONDARY, 'Not sent for approval': COLOR_ACCENT}
    fig_estado = px.bar(resumen_estado, x='Categoria', y='Importe_EUR', color='Estado_Aprobacion', title='Cumplimiento Normativo (Proporción EUR)', barmode='stack', color_discrete_map=mapa_colores)
    st.plotly_chart(fig_estado, use_container_width=True)

# AUDITORÍA
st.markdown("### Auditoría Financiera: Riesgo de Fraude (Duplicados)")
df_fraude = df_filtrado[df_filtrado['Duplicado_Fraude'] == True]
if not df_fraude.empty:
    st.error(f"⚠ Se han detectado {len(df_fraude)} registros con misma Fecha, Empleado e Importe exacto.")
    st.dataframe(df_fraude[['Fecha', 'Empleado', 'Categoria', 'Importe_EUR', 'Estado_Aprobacion']], use_container_width=True)
else:
    st.success("✅ No se han detectado pagos duplicados en la selección actual.")