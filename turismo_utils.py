import pandas as pd
import plotly.graph_objects as go
import unicodedata
import re

# ==========================================
# UTILIDADES DE TEXTO
# ==========================================
def normalize(s: str) -> str:
    """Limpieza profunda de texto."""
    if not isinstance(s, str): return str(s)
    s = s.strip().lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    return s

def get_header_info(df_raw):
    """Encuentra la fila de encabezados y la columna de estados."""
    for i in range(min(20, len(df_raw))):
        row = df_raw.iloc[i].astype(str).tolist()
        for col_idx, val in enumerate(row):
            if "etiquetas de fila" in val.lower():
                return i, col_idx
    return None, None

# ==========================================
# MOTORES DE EXTRACCIÓN
# ==========================================
def get_data_historico(xls, estado_input):
    try:
        df_raw = pd.read_excel(xls, sheet_name='Vista07a', header=None)
    except Exception as e:
        return None

    header_idx, state_col_idx = get_header_info(df_raw)
    if header_idx is None: return None

    # Leer AÑOS de la fila SUPERIOR (header_idx - 1)
    row_years = df_raw.iloc[header_idx - 1].astype(str).tolist()
    col_indices = []
    years_found = []
    
    for c_idx, val in enumerate(row_years):
        match = re.search(r'Total\s*(199\d|20[0-3]\d)', val, re.IGNORECASE)
        if match:
            col_indices.append(c_idx)
            years_found.append(int(match.group(1)))
            
    if not col_indices: return None

    # Extraer datos
    df_data = df_raw.iloc[header_idx+1:].copy()
    target = normalize(estado_input)
    # Buscamos normalizando la columna detectada
    df_data['_norm'] = df_data.iloc[:, state_col_idx].astype(str).apply(normalize)
    
    # Intento de match exacto o parcial
    row_data = df_data[df_data['_norm'] == target]
    
    # Si no encuentra exacto, intenta buscar si el string está contenido
    if row_data.empty:
        row_data = df_data[df_data['_norm'].str.contains(target, na=False)]

    if row_data.empty: return None

    vals = row_data.iloc[0, col_indices].values
    data_clean = []
    for y, v in zip(years_found, vals):
        try:
            fv = float(v)
            if pd.notna(fv):
                data_clean.append({'Año': y, 'Valor': fv})
        except:
            continue
            
    df_res = pd.DataFrame(data_clean).sort_values('Año')
    return df_res.iloc[-10:] # Últimos 10 años

def get_data_mensual(xls, estado_input):
    sheets = {'Disp': 'Vista05', 'Ocup': 'Vista06a', 'Perc': 'Vista09a'}
    data = {}
    meses_labels = []
    
    target = normalize(estado_input)

    for key, sheet in sheets.items():
        try:
            df_raw = pd.read_excel(xls, sheet_name=sheet, header=None)
            header_idx, state_col_idx = get_header_info(df_raw)
            if header_idx is None: continue
            
            # Identificar columnas de MESES
            header_row = df_raw.iloc[header_idx].astype(str).tolist()
            month_indices = []
            month_names = []
            
            for c_idx, val in enumerate(header_row):
                if re.match(r'\[\d{2}\]', val): 
                    month_indices.append(c_idx)
                    month_names.append(val)
            
            last_12_indices = month_indices[-12:]
            if key == 'Disp': 
                meses_labels = [m.split('] ')[-1] for m in month_names[-12:]]

            # Extraer valor del Estado
            df_data = df_raw.iloc[header_idx+1:].copy()
            df_data['_norm'] = df_data.iloc[:, state_col_idx].astype(str).apply(normalize)
            
            row = df_data[df_data['_norm'] == target]
            if row.empty:
                # Intento búsqueda parcial
                row = df_data[df_data['_norm'].str.contains(target, na=False)]

            if row.empty:
                data[key] = [0]*12
            else:
                vals = row.iloc[0, last_12_indices].values
                data[key] = [0 if pd.isna(x) else float(x) for x in vals]
                
        except Exception:
            return None

    if len(data) < 3: return None
    return data, meses_labels

# ==========================================
# GENERADOR DE GRÁFICAS (DEVUELVE FIGURAS)
# ==========================================
def generar_figuras(df_hist, data_men, estado, palette, font_family):
    """Genera objetos Figure de Plotly usando la paleta y fuente de Streamlit."""
    figs = {}
    
    # Colores desde la paleta de la App
    c_primary = palette[0] if len(palette) > 0 else "#1f2a44"
    c_secondary = palette[1] if len(palette) > 1 else "#889064"
    c_accent = palette[2] if len(palette) > 2 else "#ff9f18"

    # --- GRÁFICA 1: HISTÓRICO ---
    if df_hist is not None and not df_hist.empty:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_hist['Año'], y=df_hist['Valor'],
            marker_color=c_primary,
            text=[f"{x:,.0f}" for x in df_hist['Valor']],
            textposition='outside'
        ))
        
        rango = f"{df_hist['Año'].min()}-{df_hist['Año'].max()}"
        fig1.update_layout(
            title=dict(text=f"Llegada de Turistas - {estado} ({rango})", x=0),
            yaxis_title="Turistas",
            template="plotly_white",
            font=dict(family=font_family),
            height=450,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        figs['historico'] = fig1

    # --- GRÁFICA 2: MENSUAL ---
    if data_men:
        vals, meses = data_men
        fig2 = go.Figure()
        
        # Disponibles
        fig2.add_trace(go.Bar(
            x=meses, y=vals['Disp'], name="Cuartos Disponibles",
            marker_color=c_primary
        ))
        # Ocupados
        fig2.add_trace(go.Bar(
            x=meses, y=vals['Ocup'], name="Cuartos Ocupados",
            marker_color=c_secondary,
            text=[f"{x:,.0f}" for x in vals['Ocup']],
            textposition='auto'
        ))
        # Porcentaje
        perc = [x * 100 for x in vals['Perc']]
        fig2.add_trace(go.Scatter(
            x=meses, y=perc, name="% Ocupación",
            mode="lines+markers+text",
            line=dict(color=c_accent, width=3),
            text=[f"{x:.1f}%" for x in perc],
            textposition="top center",
            yaxis="y2"
        ))
        
        fig2.update_layout(
            title=dict(text=f"Actividad Hotelera (Últimos 12 Meses) - {estado}", x=0),
            yaxis_title="Cuartos",
            yaxis2=dict(title="%", overlaying="y", side="right", range=[0, 105], showgrid=False),
            barmode="group",
            template="plotly_white",
            font=dict(family=font_family),
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            height=550,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        figs['mensual'] = fig2
        
    return figs
