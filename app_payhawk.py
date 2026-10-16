import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import glob

# Configuración de página corporativa
st.set_page_config(page_title="Control Financiero - Payhawk", page_icon="📊", layout="wide")

# Paleta Corporativa (Azules)
COLOR_APPROVED = '#002244'     # Azul marino oscuro
COLOR_WAITING = '#005b9f'      # Azul corporativo medio
COLOR_NOTSENT = '#80bfff'      # Azul claro
COLOR_FACTURA = '#004080'      # Azul intenso documental
COLOR_SIN_FACTURA = '#b3d9ff'  # Azul pálido alerta

# 1. Búsqueda dinámica del archivo fuera de la caché para detectar cambios al instante
ruta_carpeta = "Datos"
archivos = sorted(
    glob.glob(os.path.join(ruta_carpeta, "*.xlsx")) + glob.glob(os.path.join(ruta_carpeta, "*.xls")),
    key=os.path.getmtime,
    reverse=True
)

@st.cache_data
def cargar_y_procesar_datos(archivo_ruta, fecha_modificacion):
    df = pd.read_excel(archivo_ruta, sheet_name='Expenses')
    
    columnas_map = {
        'Document Date': 'Fecha',
        'Expense Owner': 'Empleado',
        'Expense Category': 'Categoria',
        'Supplier Name': 'Proveedor',
        'Paid Currency': 'Divisa_Original',
        'Total Amount (EUR)': 'Importe_EUR',
        'Approval Status': 'Estado_Aprobacion',
        'Document Type': 'Tiene_Factura',
        'File 1': 'File 1',
        'File 2': 'File 2',
        'File 3': 'File 3'
    }
    
    df = df[[col for col in columnas_map.keys() if col in df.columns]].rename(columns=columnas_map)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Importe_EUR'] = pd.to_numeric(df['Importe_EUR'], errors='coerce').fillna(0.0)
    df['Categoria'] = df['Categoria'].fillna('Sin Categoría')
    df['Empleado'] = df['Empleado'].fillna('Sin Asignar')
    df['Estado_Aprobacion'] = df['Estado_Aprobacion'].fillna('Not sent for approval')

    # Mes en formato '01 - Ene', '02 - Feb' para orden cronológico exacto
    meses_abrev = {
        1: '01 - Ene', 2: '02 - Feb', 3: '03 - Mar', 4: '04 - Abr',
        5: '05 - May', 6: '06 - Jun', 7: '07 - Jul', 8: '08 - Ago',
        9: '09 - Sep', 10: '10 - Oct', 11: '11 - Nov', 12: '12 - Dic'
    }
    df['Mes'] = df['Fecha'].dt.month.map(meses_abrev).fillna('Sin Fecha')
    
    # Alerta de antigüedad (> 15 días y No Aprobado)
    dias_antiguedad = (pd.Timestamp.today().normalize() - df['Fecha']).dt.days
    df['Alerta_Antiguedad'] = np.where(
        (df['Estado_Aprobacion'] != 'Approved') & (dias_antiguedad > 15),
        'ALERTA', 'OK'
    )
    
    # Control de Factura unificado (verifica File 1, File 2 y File 3)
    tiene_adjunto = df['File 1'].notna() | df['File 2'].notna()
    if 'File 3' in df.columns:
        tiene_adjunto = tiene_adjunto | df['File 3'].notna()
    df['Control_Factura'] = np.where(tiene_adjunto, 'Con Factura', 'Sin Factura')
    
    # Regla de Auditoría: Duplicados potenciales (Misma Fecha, Empleado e Importe exacto)
    df['Duplicado_Fraude'] = df.duplicated(subset=['Fecha', 'Empleado', 'Importe_EUR'], keep=False)
    
    return df

if not archivos:
    st.error("⚠️ No se encontró ningún archivo Excel de Payhawk en la carpeta 'Datos'. Sube el fichero al repositorio.")
    st.stop()

archivo_actual = archivos[0]
mtime_actual = os.path.getmtime(archivo_actual)
df = cargar_y_procesar_datos(archivo_actual, mtime_actual)

# ==========================================
# INTERACTIVIDAD (SLICERS EN BARRA LATERAL)
# ==========================================
st.sidebar.header("Filtros del Modelo")
st.sidebar.caption(f"Archivo activo: `{os.path.basename(archivo_actual)}`")

meses_disponibles = sorted(df['Mes'].unique())
mes_filtro = st.sidebar.multiselect("Mes", options=meses_disponibles, default=meses_disponibles)

empleados_disponibles = sorted(df['Empleado'].unique())
empleado_filtro = st.sidebar.multiselect("Empleado", options=empleados_disponibles)

facturas_disponibles = sorted(df['Control_Factura'].unique())
factura_filtro = st.sidebar.multiselect("Control Factura", options=facturas_disponibles, default=facturas_disponibles)

df_filtrado = df[df['Mes'].isin(mes_filtro) & df['Control_Factura'].isin(factura_filtro)]
if empleado_filtro:
    df_filtrado = df_filtrado[df_filtrado['Empleado'].isin(empleado_filtro)]

# ==========================================
# BUSINESS VISUALIZATION (KPIs EJECUTIVOS)
# ==========================================
st.title("Dashboard Financiero Payhawk - ACK3 Global Solutions")

gasto_total = df_filtrado['Importe_EUR'].sum()
gasto_aprobado = df_filtrado[df_filtrado['Estado_Aprobacion'] == 'Approved']['Importe_EUR'].sum()
gasto_no_aprobado = gasto_total - gasto_aprobado
pct_aprobacion = (gasto_aprobado / gasto_total) * 100 if gasto_total > 0 else 0.0

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
# GRÁFICOS ANALÍTICOS (Plotly - Paleta Azul)
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    resumen_cat = (
        df_filtrado.groupby('Categoria', as_index=False)['Importe_EUR']
        .sum()
        .sort_values('Importe_EUR', ascending=True)
    )
    fig_vol = px.bar(
        resumen_cat, x='Importe_EUR', y='Categoria', orientation='h',
        title='Gasto por Categoría (Volumen EUR)',
        color_discrete_sequence=[COLOR_WAITING]
    )
    st.plotly_chart(fig_vol, width="stretch")

with col_graf2:
    resumen_estado = df_filtrado.groupby(['Categoria', 'Estado_Aprobacion'], as_index=False)['Importe_EUR'].sum()
    mapa_colores = {
        'Approved': COLOR_APPROVED,
        'Waiting approval': COLOR_WAITING,
        'Not sent for approval': COLOR_NOTSENT
    }
    fig_estado = px.bar(
        resumen_estado, x='Categoria', y='Importe_EUR', color='Estado_Aprobacion',
        title='Cumplimiento Normativo (Proporción EUR)',
        barmode='stack', color_discrete_map=mapa_colores
    )
    st.plotly_chart(fig_estado, width="stretch")

st.markdown("### Análisis Volumétrico de Justificantes")
resumen_tickets = df_filtrado.groupby(['Mes', 'Control_Factura']).size().reset_index(name='Cantidad_Tickets')
mapa_tickets = {'Con Factura': COLOR_FACTURA, 'Sin Factura': COLOR_SIN_FACTURA}
fig_tickets = px.bar(
    resumen_tickets, x='Mes', y='Cantidad_Tickets', color='Control_Factura',
    title='Tickets Subidos vs Faltantes por Mes',
    barmode='group', category_orders={'Mes': meses_disponibles}, color_discrete_map=mapa_tickets
)
st.plotly_chart(fig_tickets, width="stretch")

# ==========================================
# AUDITORÍA FINANCIERA (CONTROL DE DUPLICADOS)
# ==========================================
st.markdown("---")
st.markdown("### Auditoría Financiera: Riesgo de Fraude (Duplicados)")
df_fraude = df_filtrado[df_filtrado['Duplicado_Fraude'] == True].sort_values(by=['Fecha', 'Empleado', 'Importe_EUR'])

if not df_fraude.empty:
    st.error(f"Se han detectado {len(df_fraude)} registros con misma Fecha, Empleado e Importe exacto.")
    st.dataframe(
        df_fraude[['Fecha', 'Empleado', 'Categoria', 'Proveedor', 'Importe_EUR', 'Estado_Aprobacion', 'Control_Factura']],
        width="stretch"
    )
else:
    st.success("✅ No se han detectado pagos duplicados en la selección actual.")
