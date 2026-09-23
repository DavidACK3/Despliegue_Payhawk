git config --global user.name "DavidACK3"

git config --global user.email "david.rodriguez.ext@ack3.eu"

# 🚀 Guía Operativa de Actualización: Dashboard Financiero Payhawk (Streamlit & GitHub)

Este documento detalla el procedimiento estándar para actualizar el cuadro de mando financiero en la nube alojado en **Streamlit Cloud** y sincronizado mediante **GitHub**, de cara al cierre de reporting periódico (ej. 30 de septiembre de 2026).

---

## 📅 Protocolo de Actualización para Cierres Mensuales

Dado que la aplicación web consume la información directamente de los ficheros contenidos en el repositorio de GitHub, cualquier actualización del reporting se realiza siguiendo este flujo de trabajo:

### 1. Preparación y Depuración Local
1. **Exportación de Datos:** Descarga el nuevo extracto mensual o acumulado actualizado desde la plataforma de **Payhawk**.
2. **Ubicación en el Directorio:** Reemplaza o añade el archivo en la ruta local correspondiente de tu entorno de trabajo (respetando la estructura de columnas acordada para mantener la compatibilidad con el script).
3. **Validación Previa:** Ejecuta localmente o verifica los datos en tu entorno de desarrollo en **Visual Studio Code** para asegurar que el procesamiento de Python lee correctamente el nuevo volumen de transacciones sin errores de sintaxis o desajustes de esquema.

---

### 2. Sincronización con el Repositorio Remoto (GitHub)
Una vez validado el modelo localmente, se procede al volcado de los cambios hacia la nube:

1. Abre **Visual Studio Code** en la carpeta raíz del proyecto de despliegue.
2. Dirígete a la pestaña de **Source Control** (Control de código fuente) en el panel izquierdo.
3. Revisa los archivos modificados y haz clic en el icono **`+` (Stage Changes)** para añadirlos al commit.
4. Escribe un mensaje descriptivo y profesional en el cuadro de texto del commit indicando el periodo de actualización (ejemplo: *"Actualización de reporting financiero - Cierre 30 Septiembre 2026"*).
5. Haz clic en **Commit** y, a continuación, pulsa en **Sync Changes** (o el botón de subida/Push) para enviar los cambios a la rama principal (`main`) de tu repositorio remoto en GitHub.

---

### 3. Actualización Automática en Producción (Streamlit Cloud)
* **Intervención Cero en la Nube:** No es necesario acceder a Streamlit Cloud ni modificar parámetros en el servidor.
* **Compilación Desatendida:** Al detectar el nuevo `push` en la rama `main` de GitHub, Streamlit Cloud activará de forma automática un proceso de *rebuild* (recompilación).
* **Disponibilidad:** En menos de un minuto, la aplicación web actualizará de manera síncrona todas las métricas, tarjetas KPI y gráficos ejecutivos, reflejando fielmente los datos del nuevo cierre corporativo para la dirección y el equipo financiero de ACK3.