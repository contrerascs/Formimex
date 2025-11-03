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
    st.image('assets/Formimex.jpg', width='stretch')

#st.markdown("<h1 class='title'>Reporte de Inspección de Calidad</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Sistema interno de control de calidad - Formimex</p>", unsafe_allow_html=True)
st.write("---")

# --- FORMULARIO ---
with st.form("formulario_inspeccion"):
    st.subheader("🧰 Datos generales")
    reporte = []

    # * Campos no numéricos *
    fecha_inspeccion = st.date_input("Fecha de inspección", datetime.today())
    reporte.append(fecha_inspeccion.strftime("%m/%d/%y"))

    proveedor = st.selectbox("Proveedor", ["FORMIMEX"])
    reporte.append(proveedor)

    material = st.selectbox("Material a inspeccionar", ["MALLA 2X2 8/8", "MALLA 4X4 8/8"])
    reporte.append(material)
    if material == 'MALLA 2X2 8/8':
        materialh2 = '2X2 8/8'
    else:
        materialh2 = '4X4 8/8'

    tipo = st.selectbox("Tipo", ["MP", "PT"])
    reporte.append(tipo)

    proveedor_nuevo = st.selectbox("Proveedor nuevo", ["NO", "SI"])
    reporte.append(proveedor_nuevo)

    inspector = st.selectbox("Nombre del inspector", ["Samuel Contreras", "Mauricio Torres"])
    reporte.append(inspector)
    if inspector == 'Samuel Contreras':
        inspectorh2 = 'SAMUEL'
    else:
        inspectorh2 = 'MAURICIO'

    lote = st.selectbox("Lote de produccion", ["ROJO", "NARANJA", "MORADO", "VERDE", "ROSA", "AMARILLO", "FORMIMEX"])
    reporte.append(lote)

    st.subheader("🏗️ Datos de la malla")

    reporte.append(st.selectbox("Tipo de alambre", ["LISO", "CORRUGADO"]))

    # * Campos numéricos con number_input *
    c1, c2 = st.columns(2)
    with c1:
        cant_long = st.number_input("Cantidad de alambres (longitudinal)", min_value=1, step=1)
        reporte.append(int(cant_long))

    with c2:
        cant_trans = st.number_input("Cantidad de alambres (transversal)", min_value=1, step=1)
        reporte.append(int(cant_trans))

    c1, c2 = st.columns(2)
    with c1:
        dim_long = st.number_input("Dimension de la malla (longitudinal mm)", min_value=1.0, step=0.01)
        reporte.append(float(dim_long))

    with c2:
        dim_trans = st.number_input("Dimension de la malla (transversal mm)", min_value=1.0, step=0.01)
        reporte.append(float(dim_trans))

    reporte.append(st.selectbox("Perimetro", ["Completo", "Incompleto"]))

    c1, c2 = st.columns(2)
    with c1:
        puntas_long = st.number_input("Puntas (longitudinal)", min_value=0, step=1)
        reporte.append(int(puntas_long))
    with c2:
        puntas_trans = st.number_input("Puntas (transversal)", min_value=0, step=1)
        reporte.append(int(puntas_trans))

    c1, c2 = st.columns(2)
    with c1:
        filos_long = st.number_input("Filos (longitudinal)", min_value=0, step=1)
        reporte.append(int(filos_long))
    with c2:
        filos_trans = st.number_input("Filos (transversal)", min_value=0, step=1)
        reporte.append(int(filos_trans))

    puntos_despegados = st.number_input("Puntos despegados", min_value=0, step=1)
    reporte.append(int(puntos_despegados))

    # --- Diámetro del alambre ---
    st.subheader("📏 Medición de diámetro del alambre")

    muestras_long = []
    muestras_trans = []

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("##### Longitudinal")
        for i in range(8):
            valor = st.number_input(f"Diámetro Longitudinal {i+1} (mm)", min_value=0.01, step=0.01, key=f"long_{i}")
            muestras_long.append(float(valor))
            reporte.append(float(valor))
        promedio_long = sum(muestras_long) / len(muestras_long)
        st.info(f"**Promedio diámetro longitudinal:** {promedio_long:.2f} mm")
        reporte.append(round(promedio_long, 2))

    with col6:
        st.markdown("##### Transversal")
        for i in range(8):
            valor = st.number_input(f"Diámetro Transversal {i+1} (mm)", min_value=0.01, step=0.01, key=f"trans_{i}")
            muestras_trans.append(float(valor))
            reporte.append(float(valor))
        promedio_trans = sum(muestras_trans) / len(muestras_trans)
        st.info(f"**Promedio diámetro transversal:** {promedio_trans:.2f} mm")
        reporte.append(round(promedio_trans, 2))

    # --- Espaciamientos ---
    st.subheader("⚙️ Medición de espaciamientos")

    muestras_esp_long = []
    muestras_esp_trans = []

    col7, col8 = st.columns(2)

    with col7:
        st.markdown("##### Longitudinal")
        for i in range(8):
            valor = st.number_input(f"Espaciamiento Longitudinal {i+1} (mm)", min_value=0.01, step=0.01, key=f"esp_long_{i}")
            muestras_esp_long.append(float(valor))
            reporte.append(float(valor))
        promedio_espaciamiento_long = sum(muestras_esp_long) / len(muestras_esp_long)
        st.info(f"**Promedio espaciamiento longitudinal:** {promedio_espaciamiento_long:.2f} mm")
        reporte.append(round(promedio_espaciamiento_long, 2))

    with col8:
        st.markdown("##### Transversal")
        for i in range(8):
            valor = st.number_input(f"Espaciamiento Transversal {i+1} (mm)", min_value=0.01, step=0.01, key=f"esp_trans_{i}")
            muestras_esp_trans.append(float(valor))
            reporte.append(float(valor))
        promedio_espaciamiento_trans = sum(muestras_esp_trans) / len(muestras_esp_trans)
        st.info(f"**Promedio espaciamiento transversal:** {promedio_espaciamiento_trans:.2f} mm")
        reporte.append(round(promedio_espaciamiento_trans, 2))

    reporte.append(st.selectbox("Resistencia de los puntos de soldadura", ["10 A 25NM - 10 A 30NM"]))

    peso_malla = st.number_input("Peso de la malla (kg)", min_value=0.01, step=0.01)
    reporte.append(round(float(peso_malla), 2))

    st.subheader("📸 Observaciones")
    observaciones = st.text_area("Observaciones del inspector")

    enviado = st.form_submit_button("Guardar reporte")

    reporte_h2 = [reporte[0],reporte[1],materialh2,reporte[3],reporte[4],'1/3 del ancho de la malla terminada y longitud debe incluir al menos 3 alambres transversales.',
                  reporte[6],inspectorh2,reporte[7],reporte[7],reporte[8],reporte[9],reporte[10],reporte[11],reporte[12],reporte[12],reporte[13],
                  reporte[14],reporte[15],reporte[16],reporte[17],reporte[17],reporte[26],reporte[35],(reporte[44]*0.1),(reporte[53]*0.1),reporte[54],
                  reporte[54],reporte[55],reporte[55],observaciones]


    # ✅ VALIDACIÓN FINAL
    if enviado:
        if observaciones.strip() == "":
            st.warning("⚠️ Por favor agrega observaciones.")
        elif any(v is None for v in reporte):
            st.warning("⚠️ Todos los campos deben estar completos.")
        else:
            # ✅ Guardar en Google Sheets
            # Abrir el archivo de Google Sheets
            spreadsheet = client.open('Registro de inspeccion de calidad - Formimex')

            # Hoja 1: BASE DE DATOS
            hoja1 = spreadsheet.worksheet('BASE DE DATOS')
            hoja1.append_row(reporte, value_input_option='USER_ENTERED')

            # Hoja 2: MALLA FO-CCA-04
            hoja2 = spreadsheet.worksheet('MALLA FO-CCA-04')
            hoja2.append_row(reporte_h2, value_input_option='USER_ENTERED')

            st.success("✅ Reporte guardado correctamente.")
            st.write("### Resumen del reporte")
            st.json({
                "Inspector": reporte[5],
                "Fecha": str(reporte[0]),
                "Proveedor": reporte[1],
                "Material": reporte[2],
                "Lote": reporte[6],
                "Promedio diámetro long": promedio_long,
                "Promedio diámetro transv": promedio_trans,
                "Promedio espaciamiento long": promedio_espaciamiento_long,
                "Promedio espaciamiento transv": promedio_espaciamiento_trans,
                "Observaciones": observaciones
            })
