import base64
import re
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import json
import io
import sys
import requests
import zipfile
import shutil
import os
from PIL import Image

# Importamos el módulo personalizado
# Nota: Asegúrate de que este archivo exista en tu carpeta local
try:
    import turismo_utils
except ImportError:
    pass 

sys.path.append(".") 

# ---------------------------
# Configuración de página
# ---------------------------
st.set_page_config(
    page_title="Automatización de estudios de mercado",
    layout="wide",
    page_icon="📊"
)

# ---------------------------
# SISTEMA DE AUTENTICACIÓN
# ---------------------------
def check_password():
    """Retorna `True` si el usuario tiene la contraseña correcta."""

    def password_entered():
        """Verifica si el usuario y contraseña coinciden."""
        if (
            st.session_state["username"] == "PhiQus" and 
            st.session_state["password"] == "estudiosdemercado"
        ):
            st.session_state["password_correct"] = True
            # Borramos las credenciales de la memoria de sesión por seguridad
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # 1. Si ya está autenticado, retornar True
    if st.session_state.get("password_correct", False):
        return True

    # 2. Si no está autenticado, mostrar formulario
    
    # Un poco de estilo para centrar el login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔒 Acceso Restringido")
        st.info("Por favor, inicia sesión para acceder a la herramienta de Estudios de Mercado.")
        
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        
        if st.button("Iniciar Sesión", on_click=password_entered):
            # Si la validación falla (se ejecuta el on_click primero), mostramos error
            if not st.session_state.get("password_correct", False):
                st.error("😕 Usuario o contraseña incorrectos")

    return False

# ---------------------------
# BLOQUEO DE EJECUCIÓN
# ---------------------------
# Si check_password devuelve False, detenemos la ejecución del script aquí.
if not check_password():
    st.stop()

# ---------------------------
# CONSTANTE DE SELECCIÓN NEUTRA
# ---------------------------
OPCION_DEFAULT = "--- Selecciona un indicador ---"

# ---------------------------
# CONSTANTES GEOGRÁFICAS
# ---------------------------
ESTADOS_MEXICANOS = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
    "Durango", "Guanajuato", "Guerrero", "Hidalgo", "Jalisco",
    "México", "Michoacán", "Morelos", "Nayarit", "Nuevo León",
    "Oaxaca", "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí",
    "Sinaloa", "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala",
    "Veracruz", "Yucatán", "Zacatecas"
]

# ---------------------------
# CONSTANTES Y RUTAS: NIVEL PAÍS
# ---------------------------
OPCIONES_PAIS_ORDENADAS = [
    "PIB nacional",
    "Inflación nacional",
    "Crecimiento poblacional nacional",
    "Distribución de la población por edad",
    "Distribución de la población por sexo",
    "Población económicamente activa",
    "Población por sector de actividad económica",
    "PIB histórico total y per cápita",
    "Proyección del PIB total y per cápita",
    "Inflación histórica",
    "Tasa cambiaria histórica",
    "Flujo de inversión extranjera para un Estado",
    "Anuncio de inversión por país",
    "Ranking mundial de países por ingreso de divisas",
    "Histórico de llegadas y salidas de turistas",
    "Entradas aereas de turistas",
    "Actividad hotelera",
    "Conectividad aérea (Vuelos nacionales)",
    "Conectividad aérea (Vuelos internacionales)"
]

RUTAS_PAIS = {
    "PIB nacional": "pib_nacional.ipynb",
    "Inflación nacional": "inflacion_nacional.ipynb",
    "Crecimiento poblacional nacional": "crecimiento_poblacional_nacional.ipynb",
    "Distribución de la población por edad": "pob_distribucion_edad.ipynb",
    "Distribución de la población por sexo": "pob_distribucion_sexo.ipynb",
    "Población económicamente activa": "pob_economicamente_activa.ipynb",
    "Población por sector de actividad económica": "pob_sector_actividad.ipynb",
    "PIB histórico total y per cápita": "pib_historico_percapita.ipynb",
    "Proyección del PIB total y per cápita": "pib_proyeccion.ipynb",
    "Inflación histórica": "inflacion_historica.ipynb",
    "Tasa cambiaria histórica": "tasa_cambiaria.ipynb",
    "Flujo de inversión extranjera para un Estado": "inversion_extranjera_ied.ipynb",
    "Anuncio de inversión por país": "inversion_anuncios_pais.ipynb",
    "Ranking mundial de países por ingreso de divisas": "turismo_ranking_divisas.ipynb",
    "Histórico de llegadas y salidas de turistas": "turismo_historico_flujos.ipynb",
    "Entradas aereas de turistas": "turismo_entradas_aereas.ipynb",
    "Actividad hotelera": "turismo_actividad_hotelera.ipynb",
    "Conectividad aérea (Vuelos nacionales)": "conectividad_aerea_nacionales.ipynb",
    "Conectividad aérea (Vuelos internacionales)": "conectividad_aerea_internacionales.ipynb"
}

# ---------------------------
# CONSTANTES Y RUTAS: NIVEL ESTADO
# ---------------------------
OPCIONES_ESTADO_ORDENADAS = [
    "Población y PIB",
    "Crecimiento histórico poblacional",
    "Proyección poblacional",
    "PIB por sectores",
    "Anuncios de inversión por industria",
    "Llegada de turistas (Histórico) y ocupación de alojamiento",
    "Conecctividad terrestre"
]

RUTAS_ESTADO = {
    "Población y PIB": "estado_poblacion_pib.ipynb",
    "Crecimiento histórico poblacional": "estado_crecimiento_hist.ipynb",
    "Proyección poblacional": "estado_proyeccion.ipynb",
    "PIB por sectores": "estado_pib_sectores.ipynb",
    "Anuncios de inversión por industria": "estado_inversion_anuncios.ipynb",
    "Llegada de turistas (Histórico) y ocupación de alojamiento": "estado_turismo_llegadas.ipynb",
    "Conecctividad terrestre": "estado_conectividad.ipynb"
}

# ---------------------------
# CONSTANTES Y RUTAS: NIVEL MUNICIPIO Y LOCALIDAD
# ---------------------------
OPCIONES_MUNICIPIOS_ORDENADAS = [
    "Distribución de la población",
    "Proyección de la población"
]

RUTAS_MUNICIPIO = {
    "Distribución de la población": "municipio_distribucion_pob.ipynb",
    "Proyección de la población": "municipio_proyeccion_pob.ipynb"
}

OPCIONES_LOCALIDADES_ORDENADAS = [
    "Distribución de la población",
    "Crecimiento histórico de la población"
]

RUTAS_LOCALIDAD = {
    "Distribución de la población": "localidad_distribucion_pob.ipynb",
    "Crecimiento histórico de la población": "localidad_crecimiento_hist.ipynb"
}

# ---------------------------
# CONFIGURACIÓN DE RUTAS Y ESTILOS
# ---------------------------
from pathlib import Path
import os

# 1. Obtenemos la ruta absoluta de la carpeta donde está este script (app.py)
# Esto devolverá algo como: /mount/src/phiqus-aedm
BASE_DIR = Path(__file__).parent.resolve()

# 2. Construimos las rutas a las carpetas 'recursos' y 'scripts'
RECURSOS_DIR = BASE_DIR / "recursos"
NOTEBOOK_DIR = BASE_DIR / "scripts"

# 3. Definimos los archivos específicos
# Usamos .resolve() para evitar ambigüedades en Linux
LOCAL_FONT_PATH = str((RECURSOS_DIR / "ballingermono-light.ttf").resolve())
LOCAL_FONT_NAME = "BallingerMono Light"

logo_path = str((RECURSOS_DIR / "logo.png").resolve())

# --- DEBUG SILENCIOSO (Opcional: verás esto en los logs de la consola de Streamlit Cloud) ---
print(f"--> Ruta Base detectada: {BASE_DIR}")
print(f"--> Buscando fuente en: {LOCAL_FONT_PATH}")
print(f"--> Buscando logo en: {logo_path}")

# 4. Función de carga de fuente (Sin cambios, solo para referencia)
@st.cache_resource
def load_local_font_css(font_path: str, font_family_name: str) -> str:
    p = Path(font_path)
    if not p.exists():
        print(f"❌ Error: No se encontró la fuente en {font_path}") # Log de error
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"""
    <style>
    @font-face {{
        font-family: '{font_family_name}';
        src: url(data:font/ttf;base64,{b64}) format('truetype');
        font-weight: 300 800;
        font-style: normal;
        font-display: swap;
    }}
    </style>
    """

@st.cache_resource
def load_local_font_css(font_path: str, font_family_name: str) -> str:
    p = Path(font_path)
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"""
    <style>
    @font-face {{
        font-family: '{font_family_name}';
        src: url(data:font/ttf;base64,{b64}) format('truetype');
        font-weight: 300 800;
        font-style: normal;
        font-display: swap;
    }}
    </style>
    """

def google_font_css(family: str, weights=(300,400,500,600,700)) -> str:
    # Ajuste simple para manejar espacios en nombres de fuentes (ej. "Open Sans")
    fam_url = family.strip().replace(" ", "+")
    w = ";".join(str(x) for x in weights)
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family={fam_url}:wght@{w}&display=swap');
    </style>
    """

def apply_font_family_to_ui_and_plot(family: str):
    st.markdown(f"""
    <style>
      html, body, [class^="css"], [data-testid="stAppViewContainer"] * {{
        font-family: '{family}', sans-serif !important;
      }}
      h1, h2, h3, h4, h5, h6 {{
        font-family: '{family}', sans-serif !important;
      }}
      .js-plotly-plot .main-svg, .plotly .main-svg {{
        font-family: '{family}', sans-serif !important;
      }}
    </style>
    """, unsafe_allow_html=True)

def apply_tab_styles(active_palette: list[str]):
    active_color = active_palette[0] if active_palette else "#0576F3"
    css = f"""
    <style>
    [data-testid="stTabs"] button {{
        border-bottom: 2px solid transparent;
        transition: all 0.2s ease-in-out;
        padding-bottom: 8px;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        border-bottom: 4px solid {active_color};
        font-weight: 600;
        color: {active_color} !important;
    }}
    [data-testid="stTabs"] button[aria-selected="false"] {{
        color: #888888;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


# ---------------------------
# MOTOR DE EJECUCIÓN DE NOTEBOOKS
# ---------------------------
def execute_notebook_content(notebook_path: str, context: dict = None):
    p = Path(notebook_path)
    if not p.exists():
        return False

    # 1. Leer contenido
    if p.suffix == '.ipynb':
        try:
            with p.open('r', encoding='utf-8') as f:
                notebook = json.load(f)
            code_to_execute = "".join(
                "".join(cell.get('source', [])) + "\n\n"
                for cell in notebook.get('cells', []) if cell.get('cell_type') == 'code'
            )
        except Exception as e:
            st.error(f"Error al leer JSON: {e}")
            return True
    elif p.suffix == '.py':
        code_to_execute = p.read_text(encoding='utf-8')
    else:
        st.error(f"Formato no soportado: {p.suffix}")
        return True

    # 2. Preparar entorno
    original_stdout = sys.stdout
    original_stdin = sys.stdin

    try:
        sys.stdout = capture = io.StringIO()
        execution_context = globals().copy()
        if context:
            execution_context.update(context)

        # 3. Simular Inputs (sys.stdin)
        notebook_inputs = execution_context.pop("NOTEBOOK_INPUTS", None)
        if notebook_inputs:
            if isinstance(notebook_inputs, list):
                input_string = "\n".join(str(x) for x in notebook_inputs) + "\n"
            elif isinstance(notebook_inputs, (str, int, float)):
                input_string = str(notebook_inputs) + "\n"
            else:
                input_string = ""
            sys.stdin = io.StringIO(input_string)

        # 4. Ejecutar
        exec(code_to_execute, execution_context)

        # 5. Restaurar y Mostrar Salida
        sys.stdout = original_stdout
        sys.stdin = original_stdin

        console_output = capture.getvalue().strip()
        if console_output:
             st.text(console_output)

        return True

    except Exception as exec_e:
        sys.stdout = original_stdout
        sys.stdin = original_stdin
        st.error(f"❌ Error de Ejecución en el Notebook: {type(exec_e).__name__}")
        st.code(f"{exec_e}", language='python')
        return True

# ---------------------------
# UTILIDAD GRÁFICA DUMMY
# ---------------------------
def colors_for_n(n: int, palette: list[str]) -> list[str]:
    if n <= len(palette):
        return palette[:n]
    out = []
    i = 0
    while len(out) < n:
        out.append(palette[i % len(palette)])
        i += 1
    return out

def display_dummy_graph(active_font, active_palette, title="Demostración"):
    st.subheader(title)
    st.caption("ℹ️ Visualización de ejemplo (No se encontró el notebook real en la ruta).")

    colA, colB = st.columns([1,1])
    with colA:
        n_bars = st.slider("Barras simuladas", 3, 15, 6, key=f"dummy_n_{title}")
    with colB:
        val_max = st.number_input("Valor Máx", 100, 10000, 500, key=f"dummy_v_{title}")

    rng = np.random.default_rng(42)
    values = rng.integers(int(val_max*0.2), int(val_max), size=n_bars)
    labels = [f"Dato {i+1}" for i in range(n_bars)]

    df = pd.DataFrame({"Etiqueta": labels, "Valor": values})
    bar_colors = colors_for_n(n_bars, active_palette)

    fig = px.bar(df, x="Etiqueta", y="Valor", template="plotly_white")
    fig.update_traces(marker_color=bar_colors)
    fig.update_layout(
        font=dict(family=active_font, size=14),
        margin=dict(t=30, b=30),
        title=dict(text=f"Simulación: {title}", font=dict(size=18))
    )
    st.plotly_chart(fig, use_container_width=True)

# =======================================================
# UI PRINCIPAL
# =======================================================

# --- HEADER ---
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    # 1. Definimos la ruta relativa dinámicamente
    # Esto busca la carpeta "recursos" al lado de donde está este archivo app.py
    base_dir = Path(__file__).parent.resolve()
    logo_path = str(base_dir / "recursos" / "logo.png")
    
    # 2. Verificamos y mostramos
    if Path(logo_path).exists():
        st.image(logo_path, use_container_width=True)
    else:
        # Si falla, esto te dirá exactamente dónde lo está buscando Linux
        st.error(f"Logo no encontrado en: {logo_path}")

with col_titulo:
    st.markdown("<h2 style='text-align: right; margin:0;'>Automatización de estudios de mercado</h2>", unsafe_allow_html=True)

st.divider()

# --- CONFIGURADOR DE ESTILOS (ACTUALIZADO) ---
st.markdown("### ⚙️ Configuración de Estilos")

col_font, col_color = st.columns([1, 1], gap="large")

# 1. FUENTES
with col_font:
    st.markdown("#### 🅰️ Tipografía")
    st.markdown(load_local_font_css(LOCAL_FONT_PATH, LOCAL_FONT_NAME), unsafe_allow_html=True)
    
    font_mode = st.radio(
        "Origen de la fuente:", 
        ["Tipografía PhiQus", "Tipografía de Google Fonts"], 
        horizontal=True,
        label_visibility="collapsed"
    )

    if font_mode == "Tipografía de Google Fonts":
        # Sub-selector para elegir entre lista o manual
        google_source = st.radio(
            "Selección Google:", 
            ["Lista sugerida", "Ingresar nombre de tipografía"], 
            horizontal=True,
            label_visibility="visible"
        )

        if google_source == "Lista sugerida":
            google_presets = ["Aptos", "Roboto", "Montserrat", "Open Sans", "Lato", "Poppins", "Raleway"]
            active_font = st.selectbox("Selecciona fuente:", google_presets)
        else:
            active_font = st.text_input(
                "Nombre exacto de la fuente (Google Fonts):", 
                value="Aptos",
                help="Escribe el nombre tal cual aparece en fonts.google.com (ej. 'Playfair Display')"
            )
        
        # Aplicar CSS de Google
        if active_font:
            st.markdown(google_font_css(active_font), unsafe_allow_html=True)
    else:
        active_font = LOCAL_FONT_NAME
    
    # Aplicar estilos globales
    apply_font_family_to_ui_and_plot(active_font)

# 2. COLORES
with col_color:
    st.markdown("#### 🎨 Paleta de Colores")
    
    # Selector para volver a default o personalizar
    color_mode = st.radio(
        "Modo de color:", 
        ["Colores PhiQus", "Paleta Personalizada"], 
        horizontal=True
    )

    default_palette = ["#0576F3", "#36F48C", "#F47806", "#F479F4", "#F3F40B"]

    if color_mode == "Paleta Personalizada":
        user_colors_str = st.text_input(
            "Códigos HEX (separados por coma):", 
            placeholder="#0576F3, #36F48C...",
            help="Ingresa tus códigos de color hexadecimales."
        )
        if user_colors_str:
            # Limpieza y validación básica
            active_palette = [x.strip().upper() for x in user_colors_str.split(",") if x.strip()]
        else:
            active_palette = default_palette
    else:
        active_palette = default_palette

    # Muestra visual de colores
    st.markdown(
        "<div style='display:flex;gap:5px;margin-top:10px;'>" +
        "".join([f"<div style='width:25px;height:25px;background:{c};border-radius:4px;border:1px solid #ccc' title='{c}'></div>" for c in active_palette]) +
        "</div>", unsafe_allow_html=True
    )

apply_tab_styles(active_palette)
st.markdown("---") 

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs([
    "🦅 Datos a nivel País",
    "🗺️ Datos a nivel Estado",
    "🏙️ Datos Municipio y Localidad"
])

# -------------------------------------------------------
# TAB 1: PAIS
# -------------------------------------------------------
with tab1:
    st.subheader("Indicadores Nacionales")

    lista_pais = [OPCION_DEFAULT] + OPCIONES_PAIS_ORDENADAS
    ind_pais = st.selectbox("Indicador:", lista_pais, key="sel_pais")

    if ind_pais == OPCION_DEFAULT:
        st.info("☝️ Por favor, selecciona un indicador para generar el reporte.")
    else:
        ctx_pais = {"active_palette": active_palette, "active_font": active_font}

        if ind_pais == "Flujo de inversión extranjera para un Estado":
            st.info("Selecciona el estado a resaltar:")
            edo_ied = st.selectbox("Estado:", ESTADOS_MEXICANOS, key="ied_input_tab1")
            ctx_pais["NOTEBOOK_INPUTS"] = [edo_ied]
            ctx_pais["ESTADO_RESALTADO"] = edo_ied

        st.markdown("---")

        archivo_pais = RUTAS_PAIS.get(ind_pais)
        ejecutado_pais = False

        if archivo_pais:
            path_pais = str(Path(NOTEBOOK_DIR) / archivo_pais)
            ejecutado_pais = execute_notebook_content(path_pais, context=ctx_pais)

        if not ejecutado_pais:
            display_dummy_graph(active_font, active_palette, title=ind_pais)


# -------------------------------------------------------
# TAB 2: ESTADO
# -------------------------------------------------------
with tab2:
    st.subheader("Datos a nivel Estado")

    st.markdown("""
    <style>
        [data-testid='stFileUploaderDropzone'] div div::before {
            content: "Arrastra y suelta el archivo aquí"; 
            visibility: visible; display: block;
        }
        [data-testid='stFileUploaderDropzone'] div div { visibility: hidden; }
        [data-testid='stFileUploaderDropzone'] button { visibility: visible; }
        [data-testid='stFileUploaderDropzone'] button::after {
            content: "Examinar archivos";
            visibility: visible; display: block; position: absolute;
            background-color: white; padding: 5px 10px; top: 0; left: 0; right: 0; bottom: 0;
            border-radius: 4px; color: #31333F; font-weight: 400;
        }
    </style>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        edo_sel = st.selectbox("Estado:", ESTADOS_MEXICANOS, key="sel_edo_tab2")
    with c2:
        lista_estado = [OPCION_DEFAULT] + OPCIONES_ESTADO_ORDENADAS
        ind_edo = st.selectbox("Indicador:", lista_estado, key="sel_ind_tab2")

    st.markdown("---")

    if ind_edo == OPCION_DEFAULT:
        st.info("☝️ Selecciona un indicador para comenzar el análisis estatal.")
    else:
        if ind_edo == "Llegada de turistas (Histórico) y ocupación de alojamiento":
            
            st.markdown(f"#### 🏨 Análisis Turístico: {edo_sel}")
            
            col_controls, col_viz = st.columns([1, 2], gap="large")
            
            with col_controls:
                st.info("🛠️ **Panel de datos**")
                
                st.markdown("##### 1. Obtener Archivo")
                st.caption("Descarga el archivo Excel 6_2.xlsx directamente de DataTur.")

                if st.button("🔄 Buscar y preparar archivo", use_container_width=True):
                    with st.spinner("Descargando ZIP y extrayendo Excel..."):
                        try:
                            url = "https://datatur.sectur.gob.mx/Documentos%20compartidos/CETM2023.zip"
                            r = requests.get(url)
                            r.raise_for_status()
                            
                            zip_in_memory = zipfile.ZipFile(io.BytesIO(r.content))
                            
                            target_file = None
                            for filename in zip_in_memory.namelist():
                                if ("6.2" in filename or "6_2" in filename) and filename.endswith((".xlsx", ".xls")):
                                    target_file = filename
                                    break
                            
                            if target_file:
                                excel_bytes = zip_in_memory.read(target_file)
                                st.session_state['ready_to_download'] = excel_bytes
                                st.session_state['filename'] = os.path.basename(target_file)
                                
                                st.success("✅ Archivo encontrado y listo.")
                                st.rerun() 
                            else:
                                st.error("No se encontró el archivo 6_2.xlsx dentro del ZIP.")

                        except Exception as e:
                            st.error(f"Error de conexión o procesamiento: {e}")

                if st.session_state.get('ready_to_download') is not None and st.session_state.get('filename'):
                    st.download_button(
                        label=f"⬇️ Descargar {st.session_state['filename']}",
                        data=st.session_state['ready_to_download'],
                        file_name=st.session_state['filename'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                st.divider()

                st.markdown("##### 2. Cargar Archivo")
                st.caption("Después de deshabilitar todos los filtros, sube el archivo para generar las gráficas.")
                
                uploaded_file = st.file_uploader(
                    "Selecciona el archivo Excel", 
                    type=["xlsx", "xls"],
                    label_visibility="collapsed"
                )

            with col_viz:
                if uploaded_file is not None:
                    try:
                        xls = pd.ExcelFile(uploaded_file)
                        
                        df_hist = turismo_utils.get_data_historico(xls, edo_sel)
                        data_men = turismo_utils.get_data_mensual(xls, edo_sel)
                        
                        if df_hist is None and data_men is None:
                            st.warning(f"⚠️ No se encontraron datos válidos para **{edo_sel}**.")
                        else:
                            figs = turismo_utils.generar_figuras(
                                df_hist, data_men, edo_sel, 
                                palette=active_palette, 
                                font_family=active_font
                            )
                            
                            if 'historico' in figs:
                                st.plotly_chart(figs['historico'], use_container_width=True)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            if 'mensual' in figs:
                                st.plotly_chart(figs['mensual'], use_container_width=True)
                                
                    except Exception as e:
                        st.error(f"Error procesando el archivo: {e}")
                else:
                    st.empty()

        else:
            st.markdown(f"#### Reporte para **{edo_sel}**: {ind_edo}")
            
            ctx_edo = {
                "active_palette": active_palette,
                "active_font": active_font,
                "ESTADO_SELECCIONADO": edo_sel
            }

            archivo_edo = RUTAS_ESTADO.get(ind_edo)
            ejecutado_edo = False

            if archivo_edo:
                path_edo = str(Path(NOTEBOOK_DIR) / archivo_edo)
                ejecutado_edo = execute_notebook_content(path_edo, context=ctx_edo)

            if not ejecutado_edo:
                display_dummy_graph(active_font, active_palette, title=f"{ind_edo} - {edo_sel}")

# -------------------------------------------------------
# TAB 3: MUNICIPIO Y LOCALIDAD
# -------------------------------------------------------
with tab3:
    col_mun, col_loc = st.columns(2, gap="medium")

    # --- COLUMNA IZQUIERDA: MUNICIPIOS ---
    with col_mun:
        st.subheader("🏢 Municipios")
        
        lista_mun = [OPCION_DEFAULT] + OPCIONES_MUNICIPIOS_ORDENADAS
        ind_mun = st.selectbox("Indicador:", lista_mun, key="sel_ind_mun")

        nombre_municipio = st.text_input("Nombre del Municipio:", placeholder="Ej. Monterrey", key="txt_mun_input")

        st.markdown("---")

        if ind_mun == OPCION_DEFAULT:
            st.info("☝️ Selecciona un indicador.")
        elif not nombre_municipio:
            st.info("👆 Ingresa el nombre de un municipio.")
        else:
            archivo_mun = RUTAS_MUNICIPIO.get(ind_mun)
            ctx_mun = {
                "active_palette": active_palette,
                "active_font": active_font,
                "TIPO_NIVEL": "Municipio",
                "MUNICIPIO_SELECCIONADO": nombre_municipio,
                "NOTEBOOK_INPUTS": [nombre_municipio]
            }

            ejecutado_mun = False
            if archivo_mun:
                path_mun = str(Path(NOTEBOOK_DIR) / archivo_mun)
                ejecutado_mun = execute_notebook_content(path_mun, context=ctx_mun)

            if not ejecutado_mun:
                display_dummy_graph(active_font, active_palette, title=f"{ind_mun}\n({nombre_municipio})")

    # --- COLUMNA DERECHA: LOCALIDADES ---
    with col_loc:
        st.subheader("🏡 Localidades")
        
        lista_loc = [OPCION_DEFAULT] + OPCIONES_LOCALIDADES_ORDENADAS
        ind_loc = st.selectbox("Indicador:", lista_loc, key="sel_ind_loc")

        nombre_localidad = st.text_input("Nombre de la Localidad:", placeholder="Ej. Polanco", key="txt_loc_input")

        st.markdown("---")

        if ind_loc == OPCION_DEFAULT:
             st.info("☝️Selecciona un indicador.")
        elif not nombre_localidad:
            st.info("👆 Ingresa el nombre de una localidad.")
        else:
            archivo_loc = RUTAS_LOCALIDAD.get(ind_loc)
            ctx_loc = {
                "active_palette": active_palette,
                "active_font": active_font,
                "TIPO_NIVEL": "Localidad",
                "LOCALIDAD_SELECCIONADA": nombre_localidad,
                "NOTEBOOK_INPUTS": [nombre_localidad]
            }

            ejecutado_loc = False
            if archivo_loc:
                path_loc = str(Path(NOTEBOOK_DIR) / archivo_loc)
                ejecutado_loc = execute_notebook_content(path_loc, context=ctx_loc)

            if not ejecutado_loc:
                display_dummy_graph(active_font, active_palette, title=f"{ind_loc}\n({nombre_localidad})")