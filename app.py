import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# Define los alcances necesarios para interactuar con Sheets y Drive
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']

# Cargar las claves desde los secretos de Streamlit
service_account_info = st.secrets["firebase"]

# Crear las credenciales a partir del diccionario
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)

# Crea un cliente autorizado de gspread
client = gspread.authorize(credentials)

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Formimex - Reporte de Inspección",
    page_icon="🧾",
    layout="centered",
)

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
        /* Fondo general */
        .main {
            background-color: #f8f9fa;
        }

        /* Título y subtítulo */
        .title {
            color: #0A4D68;
            font-weight: bold;
            font-size: 28px;
            text-align: center;
            margin-bottom: 5px;
        }
        .subtitle {
            color: #088395;
            font-weight: 500;
            text-align: center;
            font-size: 16px;
        }

        /* Imagen centrada */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 10px;
        }

        /* Inputs y etiquetas */
        label, .stTextInput label, .stNumberInput label {
            font-size: 15px !important;
        }

        /* Botón */
        .stButton>button {
            background-color: #0A4D68;
            color: white;
            font-weight: bold;
            border-radius: 10px;
            padding: 12px 0px;
            width: 100%;
            font-size: 18px;
        }

        .stButton>button:hover {
            background-color: #088395;
            color: white;
        }

        /* Ajuste de texto en móviles */
        @media (max-width: 600px) {
            .title { font-size: 22px; }
            .subtitle { font-size: 14px; }
            .stTextInput label, .stNumberInput label {
                font-size: 13px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image('assets/Formimex.jpg', use_container_width=True)

st.markdown("<h1 class='title'>Reporte de Inspección de Calidad</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Sistema interno de control de calidad - Formimex</p>", unsafe_allow_html=True)
st.write("---")

# --- FORMULARIO ---
with st.form("formulario_inspeccion"):
    st.subheader("🧰 Datos generales")
    reporte = []
    
    fecha_inspeccion = st.date_input("Fecha de inspección", datetime.today())
    reporte.append(fecha_inspeccion.strftime("%m-%y-%d"))    
    reporte.append(st.selectbox("Proveedor",["FORMIMEX"]))
    reporte.append(st.selectbox("Material a inspeccionar", ["MALLA 2X2 8/8", "MALLA 4X4 8/8"]))
    reporte.append(st.selectbox("Tipo",["MP","PT"]))
    reporte.append(st.selectbox("Proveedor nuevo",["NO","SI"]))
    reporte.append(st.selectbox("Nombre del inspector",["Samuel Contreras", "Mauricio Torres"]))
    reporte.append(st.selectbox("Lote de produccion",["ROJO","NARANJA","MORADO","VERDE","ROSA","AMARILLO","FORMIMEX"]))

    st.subheader("🏗️ Datos de la malla")
    
    reporte.append(st.selectbox("Tipo de alambre",["LISO","CORRUGADO"]))

    c1, c2 = st.columns(2)
    with c1:
        reporte.append(st.text_input("Cantidad de alambres (longitudinal)", value=None, placeholder="Ingresa un numero"))

    with c2:
        reporte.append(st.text_input("Cantidad de alambres (transversal)", value=None, placeholder="Ingresa un numero"))
        

    c1, c2 = st.columns(2)
    with c1:
        reporte.append(st.text_input("Dimension de la malla (longitudinal)", value=None, placeholder="Ingresa un numero"))

    with c2:
        reporte.append(st.text_input("Dimension de la malla (transversal)", value=None, placeholder="Ingresa un numero"))

    reporte.append(st.selectbox("Perimetro",["Completo","Incompleto"]))

    c1, c2 = st.columns(2)
    with c1:
        reporte.append(st.text_input("Puntas (longitudinal)", value=None, placeholder="Ingresa un numero"))

    with c2:
        reporte.append(st.text_input("Puntas (transversal)", value=None, placeholder="Ingresa un numero"))

    c1, c2 = st.columns(2)
    with c1:
        reporte.append(st.text_input("Filos (longitudinal)", value=None, placeholder="Ingresa un numero"))

    with c2:
        reporte.append(st.text_input("Filos (transversal)", value=None, placeholder="Ingresa un numero"))
    
    puntos_input = st.text_input("Puntos despegados")
    reporte.append(int(puntos_input)) if puntos_input else 0

    # --- Diámetro del alambre ---
    st.subheader("📏 Medición de diámetro del alambre")

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("##### Longitudinal")
        muestras_long = []
        for i in range(8):
            valor = st.text_input(f"Diámetro Longitudinal {i+1} (mm)", key=f"long_{i}")
            # Convertimos el valor solo si el campo no está vacío
            try:
                reporte.append(float(valor))
                muestras_long.append(float(valor))
            except ValueError:
                pass  # si está vacío, no se agrega

        promedio_long = sum(muestras_long) / len(muestras_long) if muestras_long else 0
        st.info(f"**Promedio diámetro longitudinal:** {promedio_long:.2f} mm")
        reporte.append(promedio_long)

    with col6:
        st.markdown("##### Transversal")
        muestras_trans = []
        for i in range(8):
            valor = st.text_input(f"Diámetro Transversal {i+1} (mm)", key=f"trans_{i}")
            try:
                reporte.append(float(valor))
                muestras_trans.append(float(valor))
            except ValueError:
                pass

        promedio_trans = sum(muestras_trans) / len(muestras_trans) if muestras_trans else 0
        st.info(f"**Promedio diámetro transversal:** {promedio_trans:.2f} mm")
        reporte.append(promedio_trans)

    # --- Espaciamientos ---
    st.subheader("⚙️ Medición de espaciamientos")

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("##### Longitudinal")
        muestras_long = []
        for i in range(8):
            valor = st.text_input(f"Espaciamiento Longitudinal {i+1} (mm)", key=f"esp_long_{i}")
            # Convertimos el valor solo si el campo no está vacío
            try:
                reporte.append(float(valor))
                muestras_long.append(float(valor))
            except ValueError:
                pass  # si está vacío, no se agrega

        promedio_espaciamiento_long = sum(muestras_long) / len(muestras_long) if muestras_long else 0
        st.info(f"**Promedio espaciamiento longitudinal:** {promedio_espaciamiento_long:.2f} mm")
        reporte.append(promedio_espaciamiento_long)

    with col6:
        st.markdown("##### Transversal")
        muestras_trans = []
        for i in range(8):
            valor = st.text_input(f"Espaciamiento Transversal {i+1} (mm)", key=f"esp_trans_{i}")
            try:
                reporte.append(float(valor))
                muestras_trans.append(float(valor))
            except ValueError:
                pass

        promedio_espaciamiento_trans = sum(muestras_trans) / len(muestras_trans) if muestras_trans else 0
        st.info(f"**Promedio espaciamiento transversal:** {promedio_espaciamiento_trans:.2f} mm")
        reporte.append(promedio_espaciamiento_trans)

    reporte.append(st.selectbox("Resistencia de los puntos de soldadura",["10 A 25NM - 10 A 30NM"]))

    reporte.append(st.text_input("Peso de la malla (kg)"))

    st.subheader("📸 Observaciones")
    observaciones = st.text_area("Observaciones del inspector")

    enviado = st.form_submit_button("Guardar reporte")

    if enviado:
        #Agregamos datos a tabla de Google Sheets
        sheet = client.open('Inspeccion de calidad - Formimex - v2').sheet1
        sheet.append_row(reporte)
        print(reporte)

        st.success("✅ El reporte ha sido registrado correctamente.")
        st.write("### Resumen del reporte")
        st.json({
            "Inspector": reporte[5],
            "Fecha": str(reporte[0]),
            "Proveedor": reporte[1],
            "Material": reporte[2],
            "Lote de produccion": reporte[6],
            "Promedio espaciamiento long(mm)": promedio_espaciamiento_long,
            "Promedio espaciamiento transv(mm)": promedio_espaciamiento_trans,
            "Promedio diámetro long(mm)": promedio_long,
            "Promedio diámetro transv(mm)": promedio_trans,
            "Observaciones": observaciones
        })
