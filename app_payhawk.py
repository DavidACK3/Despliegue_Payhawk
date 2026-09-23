import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import glob

# Configuración de página
st.set_page_config(page_title="Control Financiero - Payhawk", layout="wide")

@st.cache_data
def cargar_y_procesar_datos():
    # 1. AUTOMATIZACIÓN ETL
    ruta_carpeta = "Datos"
    archivos = glob.glob(os.path.join(ruta_carpeta, "*.xlsx"))
    
    if not archivos:
        return pd.DataFrame()
        
    df = pd.read_excel(archivos[0], sheet_name='Expenses')
    
    columnas_map = {
        'Document Date': 'Fecha', 'Expense Owner': 'Empleado', 'Expense Category': 'Categoria',
        'Total Amount (EUR)': 'Importe_EUR', 'Approval Status': 'Estado_Aprobacion', 
        'File 1': 'File 1', 'File 2': 'File 2'
    }
    df = df[[col for col in columnas_map.keys() if col in df.columns]].rename(columns=columnas_map)
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Columnas calculadas
    df['Mes'] = df['Fecha'].dt.strftime('%m - %b')
    df['Alerta_Antiguedad'] = np.where((df['Estado_Aprobacion'] != 'Approved') & ((pd.Timestamp.today() - df['Fecha']).dt.days > 15), 'ALERTA', 'OK')
    df['Control_Factura'] = np.where(df['File 1'].notna() | df['File 2'].notna(), 'Con Factura', 'Sin Factura')
    
    # 4. REGLAS DE AUDITORÍA (Duplicados)
    df['Duplicado_Fraude'] = df.duplicated(subset=['Fecha', 'Empleado', 'Importe_EUR'], keep=False)
    
    return df

df = cargar_y_procesar_datos()

if df.empty:
    st.error("No se encontró ningún archivo de Payhawk en la ruta especificada.")
    st.stop()

# ==========================================
# INTERACTIVIDAD (SLICERS EN BARRA LATERAL)
# ==========================================
st.sidebar.header("Filtros del Modelo")
mes_filtro = st.sidebar.multiselect("Mes", options=df['Mes'].unique(), default=df['Mes'].unique())
empleado_filtro = st.sidebar.multiselect("Empleado", options=df['Empleado'].unique())
factura_filtro = st.sidebar.multiselect("Control Factura", options=df['Control_Factura'].unique(), default=df['Control_Factura'].unique())

# Aplicar filtros al dataframe
df_filtrado = df[df['Mes'].isin(mes_filtro) & df['Control_Factura'].isin(factura_filtro)]
if empleado_filtro:
    df_filtrado = df_filtrado[df_filtrado['Empleado'].isin(empleado_filtro)]

# ==========================================
# 3. BUSINESS VISUALIZATION (KPIs)
# ==========================================
st.title("Dashboard Financiero Payhawk")

gasto_total = df_filtrado['Importe_EUR'].sum()
gasto_aprobado = df_filtrado[df_filtrado['Estado_Aprobacion'] == 'Approved']['Importe_EUR'].sum()
gasto_no_aprobado = gasto_total - gasto_aprobado
pct_aprobacion = (gasto_aprobado / gasto_total) * 100 if gasto_total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Gasto Total (EUR)", f"€ {gasto_total:,.2f}")
col2.metric("Total No Aprobado (EUR)", f"€ {gasto_no_aprobado:,.2f}")
col3.metric("% Aprobación Global", f"{pct_aprobacion:.1f} %")

st.markdown("---")

# ==========================================
# GRÁFICOS ANALÍTICOS (Plotly)
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Gráfico 1: Volumen por categoría
    resumen_cat = df_filtrado.groupby('Categoria')['Importe_EUR'].sum().reset_index().sort_values('Importe_EUR', ascending=True)
    fig_vol = px.bar(resumen_cat, x='Importe_EUR', y='Categoria', orientation='h', title='Gasto por Categoría (Volumen)')
    st.plotly_chart(fig_vol, use_container_width=True)

with col_graf2:
    # Gráfico 2: Proporción y Cumplimiento 100% Apilado
    resumen_estado = df_filtrado.groupby(['Categoria', 'Estado_Aprobacion'])['Importe_EUR'].sum().reset_index()
    fig_estado = px.bar(resumen_estado, x='Categoria', y='Importe_EUR', color='Estado_Aprobacion', title='Cumplimiento Normativo (Proporción)', barmode='stack')
    st.plotly_chart(fig_estado, use_container_width=True)

# ==========================================
# AUDITORÍA Y TABLA DE DATOS
# ==========================================
st.markdown("### Auditoría Financiera: Riesgo de Fraude (Duplicados)")
df_fraude = df_filtrado[df_filtrado['Duplicado_Fraude'] == True]
if not df_fraude.empty:
    st.error(f"Se han detectado {len(df_fraude)} registros con misma Fecha, Empleado e Importe exacto.")
    st.dataframe(df_fraude[['Fecha', 'Empleado', 'Categoria', 'Importe_EUR', 'Estado_Aprobacion']])
else:
    st.success("No se han detectado pagos duplicados en la selección actual.")