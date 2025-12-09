# turismo_backend.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
import urllib.request
import zipfile
import shutil
import tempfile
import io

# Intento de importar win32 solo si es necesario y está disponible
try:
    import win32com.client as win32
except ImportError:
    win32 = None

# === CONFIGURACIÓN ===
ZIP_URL = "https://datatur.sectur.gob.mx/Documentos%20compartidos/CETM2023.zip"
TARGET_FILE = "6_2.xlsx" # Nombre dentro del zip
CLEAN_FILE = "6_2_nofiltro.xlsx" # Nombre final

# === 1. ETL CON CACHÉ (Solo corre una vez) ===

@st.cache_resource(show_spinner="Descargando datos de Turismo...")
def obtener_datos_turismo(base_dir: str):
    """Descarga y extrae el Excel usando solo librerías nativas."""
    
    base_path = Path(base_dir)
    out_path = base_path / CLEAN_FILE
    
    # Si ya existe, lo retornamos directo
    if out_path.exists():
        return out_path

    # Descarga
    try:
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            zip_bytes = resp.read()
            
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            # Buscar el archivo sin importar mayúsculas/minúsculas
            target = next((n for n in zf.namelist() if TARGET_FILE.lower() in n.lower()), None)
            
            if not target:
                st.error("Archivo Excel no encontrado en el ZIP de Sectur.")
                return None
            
            # Extraer directamente al destino final (sin abrir Excel)
            with zf.open(target) as source, open(out_path, "wb") as dest:
                shutil.copyfileobj(source, dest)
                
        return out_path

    except Exception as e:
        st.error(f"Error en descarga/extracción: {e}")
        return None

@st.cache_data
def cargar_dfs_ocupacion(file_path):
    """Carga los DataFrames en memoria rápida."""
    try:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        return {
            "Vista05": pd.read_excel(xls, "Vista05", header=12),
            "Vista06a": pd.read_excel(xls, "Vista06a", header=12),
            "Vista09a": pd.read_excel(xls, "Vista09a", header=12)
        }
    except Exception as e:
        st.error(f"Error leyendo Excel: {e}")
        return {}

# === 2. GENERACIÓN DE GRÁFICAS (Dinámicas) ===

def normalizar(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).lower()) 
                   if unicodedata.category(c) != 'Mn')

def get_grafica_ocupacion(dfs, estado, palette, font_family):
    """Genera la figura Plotly usando los estilos de la App."""
    
    # Lógica de extracción (igual que tu script previo)
    v05, v06, v09 = dfs["Vista05"], dfs["Vista06a"], dfs["Vista09a"]
    
    # Helper para buscar fila
    def get_row(df, state):
        # Asumiendo col 0 son las etiquetas
        label_col = df.columns[0]
        # Filtrar normalizando
        found = df[df[label_col].astype(str).apply(normalizar) == normalizar(state)]
        if found.empty: return None
        # Columnas de tiempo (las ultimas 12 que empiezan con "[")
        cols = [c for c in df.columns if str(c).startswith("[")][-12:]
        return found[cols].values.flatten()

    disp = get_row(v05, estado)
    ocup = get_row(v06, estado)
    porc = get_row(v09, estado)

    if disp is None:
        return None # No hay datos

    # Limpieza nans
    porc = [0 if pd.isna(x) else (x*100 if x <= 1 else x) for x in porc]
    disp = [0 if pd.isna(x) else x for x in disp]
    ocup = [0 if pd.isna(x) else x for x in ocup]
    
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    # === PLOTLY CON ESTILOS DE LA APP ===
    fig = go.Figure()
    
    # Usamos la paleta dinámica de la app
    color_bar1 = palette[0] if len(palette) > 0 else "#1f2a44"
    color_bar2 = palette[1] if len(palette) > 1 else "#889064"
    color_line = palette[2] if len(palette) > 2 else "#ff9f18"

    fig.add_trace(go.Bar(
        x=meses, y=disp, name="Disponibles",
        marker_color=color_bar1, yaxis="y",
        text=[f"{int(x):,}" for x in disp], textposition="auto"
    ))

    fig.add_trace(go.Bar(
        x=meses, y=ocup, name="Ocupados",
        marker_color=color_bar2, yaxis="y",
        text=[f"{int(x):,}" for x in ocup], textposition="auto"
    ))

    fig.add_trace(go.Scatter(
        x=meses, y=porc, name="% Ocupación",
        mode="lines+markers", line=dict(color=color_line, width=3), yaxis="y2",
        hovertemplate="%{y:.1f}%"
    ))

    fig.update_layout(
        title=dict(text=f"Alojamiento: {estado}", x=0.5),
        font=dict(family=font_family, size=14), # <--- FUENTE DE LA APP
        yaxis=dict(title="Cuartos", side="left", showgrid=False),
        yaxis2=dict(title="%", overlaying="y", side="right", range=[0, 100], showgrid=False),
        barmode="group",
        template="plotly_white",
        legend=dict(orientation="h", y=-0.2),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig