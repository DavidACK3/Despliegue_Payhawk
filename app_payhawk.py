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
    ruta_carpeta = r"C:\Users\David\Desktop\Contabilidad\Reporting - Payhawk\Archivo Bruto"
    archivos = glob.glob(os.path.join(ruta_carpeta, "*.xlsx"))
    
    if not archivos:
        return pd.DataFrame()
        
    df = pd.read_excel(archivos[0], sheet_name='Expenses')
    
    columnas_map = {
        'Document Date': 'Fecha', 'Expense Owner': 'Empleado', 'Expense Category': 'Categoria',
        'Total Amount (EUR)': 'Importe_EUR', 'Approval Status': 'Estado_Aprobacion', 
        'Document Type': 'Tiene_Factura', 'File 1': 'File 1', 'File 2': 'File 2'
    }
    df = df[[col for col in columnas_map.keys() if col in df.columns]].rename(columns=columnas_map)
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Traducción y ordenación de meses
    meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
    df['Mes'] = df['Fecha'].dt.month.map(meses_es)
    
    # Columnas calculadas
    df['Alerta_Antiguedad'] = np.where((df['Estado_Aprobacion'] != 'Approved') & ((pd.Timestamp.today() - df['Fecha']).dt.days > 15), 'ALERTA', 'OK')
    df['Control_Factura'] = np.where(df['File 1'].notna() | df['File 2'].notna(), 'Con Factura', 'Sin Factura')
    
    # Auditoría Duplicados
    df['Duplicado_Fraude'] = df.duplicated(subset=['Fecha', 'Empleado', 'Importe_EUR'], keep=False)
    
    return df

df = cargar_y_procesar_datos()

if df.empty:
    st.error("No se encontró ningún archivo de Payhawk en la ruta especificada.")
    st.stop()

# Definir el orden cronológico para Slicers y Gráficos
orden_meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
meses_presentes = [m for m in orden_meses if m in df['Mes'].unique()]

# Paleta Corporativa (Azules)
color_approved = '#002244' # Azul marino oscuro
color_waiting = '#005b9f'  # Azul corporativo medio
color_notsent = '#80bfff'  # Azul claro
color_factura = '#004080'
color_sin_factura = '#b3d9ff'

# ==========================================
# INTERACTIVIDAD (SLICERS)
# ==========================================
st.sidebar.header("Filtros del Modelo")
mes_filtro = st.sidebar.multiselect("Mes", options=meses_presentes, default=meses_presentes)
empleado_filtro = st.sidebar.multiselect("Empleado", options=df['Empleado'].unique())
factura_filtro = st.sidebar.multiselect("Control Factura", options=df['Control_Factura'].unique(), default=df['Control_Factura'].unique())

df_filtrado = df[df['Mes'].isin(mes_filtro) & df['Control_Factura'].isin(factura_filtro)]
if empleado_filtro:
    df_filtrado = df_filtrado[df_filtrado['Empleado'].isin(empleado_filtro)]

# ==========================================
# VISUALIZATION (KPIs)
# ==========================================
st.title("Dashboard Financiero Payhawk")

gasto_total = df_filtrado['Importe_EUR'].sum()
gasto_aprobado = df_filtrado[df_filtrado['Estado_Aprobacion'] == 'Approved']['Importe_EUR'].sum()
gasto_no_aprobado = gasto_total - gasto_aprobado
pct_aprobacion = (gasto_aprobado / gasto_total) * 100 if gasto_total > 0 else 0

total_tickets = len(df_filtrado)
tickets_sin_factura = len(df_filtrado[df_filtrado['Control_Factura'] == 'Sin Factura'])

col1, col2, col3 = st.columns(3)
col1.metric("Gasto Total (EUR)", f"€ {gasto_total:,.2f}")
col2.metric("Total No Aprobado (EUR)", f"€ {gasto_no_aprobado:,.2f}")
col3.metric("% Aprobación Global", f"{pct_aprobacion:.1f} %")

col4, col5 = st.columns(2)
col4.metric("Total Tickets / Facturas", f"{total_tickets:,}")
col5.metric("Tickets Sin Factura (Faltantes)", f"{tickets_sin_factura:,}")

st.markdown("---")

# ==========================================
# GRÁFICOS (Plotly - Paleta Azul)
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    resumen_cat = df_filtrado.groupby('Categoria')['Importe_EUR'].sum().reset_index().sort_values('Importe_EUR', ascending=True)
    fig_vol = px.bar(resumen_cat, x='Importe_EUR', y='Categoria', orientation='h', title='Gasto por Categoría (Volumen EUR)', color_discrete_sequence=[color_waiting])
    st.plotly_chart(fig_vol, width="stretch")

with col_graf2:
    resumen_estado = df_filtrado.groupby(['Categoria', 'Estado_Aprobacion'])['Importe_EUR'].sum().reset_index()
    mapa_colores = {'Approved': color_approved, 'Waiting approval': color_waiting, 'Not sent for approval': color_notsent}
    fig_estado = px.bar(resumen_estado, x='Categoria', y='Importe_EUR', color='Estado_Aprobacion', title='Cumplimiento Normativo (Proporción EUR)', barmode='stack', color_discrete_map=mapa_colores)
    st.plotly_chart(fig_estado, width="stretch")

st.markdown("### Análisis Volumétrico de Justificantes")
resumen_tickets = df_filtrado.groupby(['Mes', 'Control_Factura']).size().reset_index(name='Cantidad_Tickets')
mapa_tickets = {'Con Factura': color_factura, 'Sin Factura': color_sin_factura}
fig_tickets = px.bar(resumen_tickets, x='Mes', y='Cantidad_Tickets', color='Control_Factura', title='Tickets Subidos vs Faltantes por Mes', barmode='group', category_orders={'Mes': meses_presentes}, color_discrete_map=mapa_tickets)
st.plotly_chart(fig_tickets, width="stretch")

# ==========================================
# AUDITORÍA DE DATOS
# ==========================================
st.markdown("### Auditoría Financiera: Riesgo de Fraude (Duplicados)")
df_fraude = df_filtrado[df_filtrado['Duplicado_Fraude'] == True]
if not df_fraude.empty:
    st.error(f"Se han detectado {len(df_fraude)} registros con misma Fecha, Empleado e Importe exacto.")
    st.dataframe(df_fraude[['Fecha', 'Empleado', 'Categoria', 'Importe_EUR', 'Estado_Aprobacion']])
else:
    st.success("No se han detectado pagos duplicados en la selección actual.")
