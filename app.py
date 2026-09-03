import streamlit as st
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from decimal import Decimal, ROUND_DOWN
import random

import historico as hist

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
    layout="centered"
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

# --- FUNCIONES COMPARTIDAS ---

def construir_reporte_h2(reporte, observaciones):
    """Traduce la fila de BASE DE DATOS al formato de la hoja MALLA FO-CCA-04."""
    materialh2 = '2X2 8/8' if reporte[2] == 'MALLA 2X2 8/8' else '4X4 8/8'
    inspectorh2 = 'SAMUEL' if reporte[5] == 'Samuel Contreras' else 'FERNANDO'
    return [reporte[0], reporte[1], materialh2, reporte[3], reporte[4],
            '1/3 del ancho de la malla terminada y longitud debe incluir al menos 3 alambres transversales.',
            reporte[6], inspectorh2, reporte[7], reporte[7], reporte[8], reporte[9],
            reporte[10], reporte[11], reporte[12], reporte[12], reporte[13],
            reporte[14], reporte[15], reporte[16], reporte[17], reporte[17],
            reporte[26], reporte[35], (reporte[44] * 0.1), (reporte[53] * 0.1),
            reporte[54], reporte[54], reporte[57], reporte[57], observaciones]


def guardar_reporte(reporte, reporte_h2):
    """Escribe el registro en las dos hojas del libro de Google Sheets."""
    spreadsheet = client.open('Registro de inspeccion de calidad - Formimex')
    spreadsheet.worksheet('BASE DE DATOS').append_row(
        reporte, value_input_option='USER_ENTERED')
    spreadsheet.worksheet('MALLA FO-CCA-04').append_row(
        reporte_h2, value_input_option='USER_ENTERED')


@st.cache_data(ttl=900, show_spinner='Analizando registros históricos...')
def cargar_tendencias(_cliente):
    """Carga la base y agrupa los registros limpios. Se refresca cada 15 min."""
    filas, origen = hist.cargar_registros(_cliente)
    indice, descartados = hist.construir_indice(filas)
    return indice, origen, len(filas), descartados


# --- ENCABEZADO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image('assets/Formimex.jpg', width='stretch')

#st.markdown("<h1 class='title'>Reporte de Inspección de Calidad</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Sistema interno de control de calidad - Formimex</p>", unsafe_allow_html=True)
st.write("---")

tab_completo, tab_rapido = st.tabs(["📝 Reporte completo", "⚡ Reporte rápido"])

# --- FORMULARIO ---
with tab_completo, st.form("formulario_inspeccion"):
    st.subheader("🧰 Datos generales")
    reporte = []

    # * Campos no numéricos *
    fecha_inspeccion = st.date_input("Fecha de inspección", datetime.today())
    reporte.append(fecha_inspeccion.strftime("%d-%m-%y"))

    proveedor = st.selectbox("Proveedor", ["FORMIMEX"],  index=None, placeholder="Selecciona el proveedor")
    reporte.append(proveedor)

    material = st.selectbox("Material a inspeccionar", ["MALLA 2X2 8/8", "MALLA 4X4 8/8"], index=None, placeholder="Selecciona el material")
    reporte.append(material)

    tipo = st.selectbox("Tipo", ["MP", "PT"], index=None, placeholder="Selecciona el tipo")
    reporte.append(tipo)

    proveedor_nuevo = st.selectbox("Proveedor nuevo", ["NO", "SI"], index=None, placeholder="Selecciona si es un nuevo proveedor")
    reporte.append(proveedor_nuevo)

    inspector = st.selectbox("Nombre del inspector", ["Samuel Contreras"], index=None, placeholder="Selecciona un inspector")
    reporte.append(inspector)

    lote = st.selectbox("Lote de produccion", ["ROJO", "NARANJA", "MORADO", "VERDE", "ROSA", "AMARILLO", "FORMIMEX"], index=None, placeholder="Selecciona un lote de produccion")
    reporte.append(lote)

    st.subheader("🏗️ Datos de la malla")

    reporte.append(st.selectbox("Tipo de alambre", ["LISO", "CORRUGADO"], index=None, placeholder="Selecciona el tipo de alambre"))

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
        dim_long = st.number_input("Dimension de la malla (longitudinal cm)", min_value=1.0, step=0.01)
        reporte.append(float(dim_long))

    with c2:
        dim_trans = st.number_input("Dimension de la malla (transversal cm)", min_value=1.0, step=0.01)
        reporte.append(float(dim_trans))

    reporte.append(st.selectbox("Perimetro", ["COMPLETO", "INCOMPLETO"], index=None, placeholder='Selecciona una opción'))

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

    resistencia = st.selectbox("Resistencia de los puntos de soldadura", ["10 A 278.61KG - SI CUMPLEN", "10 A 278.61KG - NO CUMPLEN"],
                                index=None, placeholder="Selecciona una opción")
    
    # Siempre agregar la etiqueta del campo
    reporte.append('10 A 278.61KG')

    # Si no seleccionó nada → colocar None
    if resistencia is None:
        reporte.append(None)
    else:
        # Colocar el resultado según la opción seleccionada
        if "SI CUMPLEN" in resistencia:
            reporte.append('LOS PUNTOS SI RESISTEN')
        else:
            reporte.append('LOS PUNTOS NO RESISTEN')

    resistencia_no = st.number_input("Cantidad de puntos despegados", min_value=0, step=1)
    reporte.append(int(resistencia_no))

    peso_malla = st.number_input("Peso de la malla (kg)", min_value=0.01, step=0.01)
    reporte.append(round(float(peso_malla), 2))

    st.subheader("📸 Observaciones")
    observaciones = st.text_area("Observaciones del inspector")

    enviado = st.form_submit_button("Guardar reporte")

    # ✅ VALIDACIÓN FINAL
    if enviado:
        if observaciones.strip() == "":
            st.warning("⚠️ Por favor agrega observaciones.")
        elif any(v is None for v in reporte):
            st.warning("⚠️ Todos los campos deben estar completos.")
        else:
            # ✅ Guardar en Google Sheets
            guardar_reporte(reporte, construir_reporte_h2(reporte, observaciones))

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


# ==========================================================================
# REPORTE RAPIDO
# ==========================================================================
# Autocompleta el reporte con los valores tipicos historicos de la
# combinacion Proveedor + Malla + Dimension + Alambre. Los valores son una
# PROPUESTA: el inspector debe contrastarlos con la pieza antes de guardar.

with tab_rapido:
    st.subheader("⚡ Reporte rápido")
    st.caption(
        "Captura solo los datos de identificación; el resto se propone a partir "
        "de la tendencia histórica de esa combinación. **Revisa y corrige** "
        "cada medición contra la pieza física antes de guardar."
    )

    indice, origen, n_total, n_descartados = cargar_tendencias(client)

    if not indice:
        st.error("No se pudo leer la base de datos de registros históricos.")
        st.stop()

    st.caption(
        f"Fuente: {origen} · {n_total} registros leídos · "
        f"{n_descartados} descartados por anomalías o captura incompleta."
    )

    # ---------------- Paso 1: datos de identificación ----------------
    with st.container(border=True):
        st.markdown("##### 1. Datos de identificación")

        c1, c2 = st.columns(2)
        with c1:
            rr_fecha = st.date_input("Fecha", datetime.today(), key="rr_fecha")
            rr_proveedor = st.selectbox("Proveedor", hist.PROVEEDORES,
                                        index=None, key="rr_proveedor",
                                        placeholder="Selecciona el proveedor")
        with c2:
            rr_malla = st.selectbox("Tipo de material / malla", hist.TIPOS_MALLA,
                                    index=None, key="rr_malla",
                                    placeholder="Selecciona el tipo de malla")
            rr_alambre = st.selectbox("Tipo de alambre", hist.TIPOS_ALAMBRE,
                                      index=None, key="rr_alambre",
                                      placeholder="Selecciona el tipo de alambre")

        # La malla 2x2 solo existe en 3.0 m x 1.8 m: se fija automáticamente.
        opciones_dim = hist.DIMENSIONES_POR_MALLA.get(rr_malla, [])
        if rr_malla == "2x2":
            rr_dimension = opciones_dim[0]
            st.selectbox("Dimensiones de la malla", opciones_dim, index=0,
                         disabled=True, key="rr_dim_fija",
                         help="La malla 2x2 solo se fabrica en esta medida.")
        elif rr_malla == "4x4":
            rr_dimension = st.selectbox("Dimensiones de la malla", opciones_dim,
                                        index=None, key="rr_dim_libre",
                                        placeholder="Selecciona la dimensión")
        else:
            rr_dimension = None
            st.selectbox("Dimensiones de la malla", [], index=None,
                         disabled=True, key="rr_dim_vacia",
                         placeholder="Selecciona primero el tipo de malla")

        rr_variar = st.checkbox(
            "Variar las medidas en cada generación",
            value=True, key="rr_variar",
            help="Cada reporte cae en un punto distinto de la dispersión que "
                 "ese proveedor ha mostrado históricamente (dimensiones, peso, "
                 "diámetros y espaciamientos). Desactivado, entrega siempre el "
                 "valor central de la tendencia.")

        completo = None not in (rr_proveedor, rr_malla, rr_dimension, rr_alambre)
        if st.button("⚡ Generar Reporte Rápido", key="rr_generar",
                     disabled=not completo):
            # Semilla nueva en cada generación: dos reportes de la misma
            # combinación y el mismo día deben salir con medidas distintas.
            # Se conserva como folio para poder reproducir el reporte luego.
            semilla = random.randrange(1, 2**32)
            perfil = hist.predecir_perfil(indice, rr_proveedor, rr_malla,
                                          rr_dimension, rr_alambre,
                                          semilla=semilla, variar=rr_variar)
            if perfil is None:
                st.error("No hay registros históricos suficientes para esa "
                         "combinación.")
            else:
                perfil['_folio'] = semilla
                st.session_state.rr_perfil = perfil
                st.session_state.rr_contexto = (rr_fecha, rr_proveedor, rr_malla,
                                                rr_dimension, rr_alambre)
                # Renueva las claves para que los widgets tomen los valores nuevos.
                st.session_state.rr_version = st.session_state.get("rr_version", 0) + 1

    # ---------------- Paso 2: revisión y ajuste ----------------
    perfil = st.session_state.get("rr_perfil")
    if perfil:
        fecha_rr, prov_rr, malla_rr, dim_rr, alambre_rr = st.session_state.rr_contexto
        v = st.session_state.rr_version

        def k(nombre):
            """Clave de widget versionada por generación del reporte."""
            return f"rr_{nombre}_{v}"

        st.markdown("##### 2. Revisión de los valores propuestos")
        m1, m2, m3 = st.columns(3)
        m1.metric("Registros de respaldo", perfil["_n"])
        m2.metric("Malla", f"{malla_rr} · {dim_rr}")
        m3.metric("Alambre", alambre_rr.capitalize())
        st.caption(
            f"Tendencia calculada sobre: {perfil['_nivel']} · "
            f"{perfil['_n']} de {perfil['_n_nivel']} registros comparten el "
            f"armado dominante (mismo número de alambres) · "
            f"folio de generación {perfil.get('_folio', '—')}"
        )

        if perfil["_n"] < hist.MIN_REGISTROS:
            st.warning(
                f"⚠️ Solo hay {perfil['_n']} registro(s) históricos para esta "
                "combinación. Verifica cada valor con especial cuidado."
            )
        if "geometria calculada" in perfil["_nivel"]:
            st.warning(
                "⚠️ No existe historial de esta dimensión: las medidas y el peso "
                "se calcularon a partir de la geometría nominal."
            )

        with st.form(f"rr_form_{v}"):
            st.markdown("**Datos generales**")
            g1, g2 = st.columns(2)
            with g1:
                rr_tipo = st.selectbox("Tipo", ["MP", "PT"], key=k("tipo"),
                                       index=["MP", "PT"].index(perfil["tipo"]))
                rr_prov_nuevo = st.selectbox(
                    "Proveedor nuevo", ["NO", "SI"], key=k("prov_nuevo"),
                    index=["NO", "SI"].index(perfil["proveedor_nuevo"]))
            with g2:
                rr_inspector = st.selectbox(
                    "Nombre del inspector",
                    ["Samuel Contreras"], key=k("inspector"))
                rr_perimetro = st.selectbox(
                    "Perímetro", ["COMPLETO", "INCOMPLETO"], key=k("perimetro"),
                    index=0 if perfil["perimetro"].upper() == "COMPLETO" else 1)

            st.markdown("**Alambres y dimensiones**")
            a1, a2 = st.columns(2)
            with a1:
                rr_cant_long = st.number_input(
                    "Cantidad de alambres (longitudinal)", min_value=1, step=1,
                    value=int(perfil["cant_long"]), key=k("cant_long"))
                rr_dim_long = st.number_input(
                    "Dimensión de la malla (longitudinal cm)", min_value=1.0,
                    step=0.1, value=float(perfil["dim_long"]), key=k("dim_long"))
                rr_puntas_long = st.number_input(
                    "Puntas (longitudinal)", min_value=0, step=1,
                    value=int(perfil["puntas_long"]), key=k("puntas_long"))
                rr_filos_long = st.number_input(
                    "Filos (longitudinal)", min_value=0, step=1,
                    value=int(perfil["filos_long"]), key=k("filos_long"))
            with a2:
                rr_cant_trans = st.number_input(
                    "Cantidad de alambres (transversal)", min_value=1, step=1,
                    value=int(perfil["cant_trans"]), key=k("cant_trans"))
                rr_dim_trans = st.number_input(
                    "Dimensión de la malla (transversal cm)", min_value=1.0,
                    step=0.1, value=float(perfil["dim_trans"]), key=k("dim_trans"))
                rr_puntas_trans = st.number_input(
                    "Puntas (transversal)", min_value=0, step=1,
                    value=int(perfil["puntas_trans"]), key=k("puntas_trans"))
                rr_filos_trans = st.number_input(
                    "Filos (transversal)", min_value=0, step=1,
                    value=int(perfil["filos_trans"]), key=k("filos_trans"))

            rr_puntos_desp = st.number_input(
                "Puntos despegados", min_value=0, step=1,
                value=int(perfil["puntos_despegados"]), key=k("puntos_desp"))

            st.markdown("**Mediciones individuales**")
            st.caption("Los promedios se recalculan con lo que dejes aquí.")

            def bloque(titulo, campo, etiqueta, minimo, paso):
                """Ocho lecturas editables; devuelve la lista de valores."""
                valores = []
                with st.expander(titulo, expanded=False):
                    cols = st.columns(4)
                    for i, base in enumerate(perfil[campo]):
                        with cols[i % 4]:
                            valores.append(float(st.number_input(
                                f"{etiqueta} {i + 1}", min_value=minimo, step=paso,
                                value=float(base), key=k(f"{campo}_{i}"))))
                return valores

            d1, d2 = st.columns(2)
            with d1:
                rr_diam_long = bloque("📏 Diámetro longitudinal (mm)",
                                      "diam_long", "DL", 0.01, 0.01)
                rr_esp_long = bloque("⚙️ Espaciamiento longitudinal (mm)",
                                     "esp_long", "EL", 0.01, 0.01)
            with d2:
                rr_diam_trans = bloque("📏 Diámetro transversal (mm)",
                                       "diam_trans", "DT", 0.01, 0.01)
                rr_esp_trans = bloque("⚙️ Espaciamiento transversal (mm)",
                                      "esp_trans", "ET", 0.01, 0.01)

            prom_dl = round(sum(rr_diam_long) / len(rr_diam_long), 2)
            prom_dt = round(sum(rr_diam_trans) / len(rr_diam_trans), 2)
            prom_el = round(sum(rr_esp_long) / len(rr_esp_long), 2)
            prom_et = round(sum(rr_esp_trans) / len(rr_esp_trans), 2)

            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Prom. Ø long", f"{prom_dl:.2f} mm")
            p2.metric("Prom. Ø transv", f"{prom_dt:.2f} mm")
            p3.metric("Prom. esp. long", f"{prom_el:.2f} mm")
            p4.metric("Prom. esp. transv", f"{prom_et:.2f} mm")

            st.markdown("**Soldadura y peso**")
            s1, s2 = st.columns(2)
            with s1:
                rr_resistencia = st.selectbox(
                    "Resistencia de los puntos de soldadura",
                    ["10 A 278.61KG - SI CUMPLEN",
                     "10 A 278.61KG - NO CUMPLEN"],
                    key=k("resistencia"),
                    index=0 if "SI" in perfil["resultado_soldadura"] else 1)
                rr_peso = st.number_input(
                    "Peso de la malla (kg)", min_value=0.01, step=0.01,
                    value=float(perfil["peso"]), key=k("peso"))
            with s2:
                rr_resistencia_no = st.number_input(
                    "Cantidad de puntos despegados", min_value=0, step=1,
                    value=int(perfil["pts_despegados_resistencia"]),
                    key=k("resistencia_no"))

            rr_observaciones = st.text_area(
                "Observaciones del inspector", key=k("observaciones"))

            rr_confirmado = st.checkbox(
                "Confirmo que verifiqué físicamente estas mediciones",
                key=k("confirmado"))
            rr_guardar = st.form_submit_button("💾 Guardar reporte rápido")

            if rr_guardar:
                if rr_observaciones.strip() == "":
                    st.warning("⚠️ Por favor agrega observaciones.")
                elif not rr_confirmado:
                    st.warning("⚠️ Debes confirmar la verificación física antes "
                               "de guardar.")
                else:
                    reporte = (
                        [fecha_rr.strftime("%d-%m-%y"), "FORMIMEX",
                         hist.MATERIAL_POR_MALLA[malla_rr], rr_tipo,
                         rr_prov_nuevo, rr_inspector, prov_rr,
                         alambre_rr, int(rr_cant_long), int(rr_cant_trans),
                         float(rr_dim_long), float(rr_dim_trans), rr_perimetro,
                         int(rr_puntas_long), int(rr_puntas_trans),
                         int(rr_filos_long), int(rr_filos_trans),
                         int(rr_puntos_desp)]
                        + rr_diam_long + [prom_dl]
                        + rr_diam_trans + [prom_dt]
                        + rr_esp_long + [prom_el]
                        + rr_esp_trans + [prom_et]
                        + ["10 A 278.61KG",
                           "LOS PUNTOS SI RESISTEN" if "SI CUMPLEN" in rr_resistencia
                           else "LOS PUNTOS NO RESISTEN",
                           int(rr_resistencia_no), round(float(rr_peso), 2)]
                    )
                    guardar_reporte(
                        reporte, construir_reporte_h2(reporte, rr_observaciones))

                    st.success("✅ Reporte rápido guardado correctamente.")
                    st.write("### Resumen del reporte")
                    st.json({
                        "Inspector": reporte[5],
                        "Fecha": str(reporte[0]),
                        "Proveedor": reporte[6],
                        "Material": reporte[2],
                        "Dimensión": dim_rr,
                        "Tipo de alambre": reporte[7],
                        "Promedio diámetro long": prom_dl,
                        "Promedio diámetro transv": prom_dt,
                        "Promedio espaciamiento long": prom_el,
                        "Promedio espaciamiento transv": prom_et,
                        "Peso": reporte[57],
                        "Observaciones": rr_observaciones,
                    })
