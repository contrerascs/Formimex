"""
historico.py - Analisis de tendencias sobre los registros historicos de inspeccion.

Lee la hoja 'BASE DE DATOS' (Google Sheets en linea, con respaldo al archivo
.xlsx de la carpeta assets), descarta registros atipicos o con errores de
captura, y calcula los valores tipicos esperados para cada combinacion de
Lote de produccion + Material + Dimension + Tipo de alambre.

Solo usa la libreria estandar de Python (mas gspread cuando hay conexion),
para no agregar dependencias nuevas al despliegue.
"""

import os
import re
import math
import random
import zipfile
import statistics
import xml.etree.ElementTree as ET
from collections import Counter

# --------------------------------------------------------------------------
# 1. ESTRUCTURA DE LA BASE DE DATOS
# --------------------------------------------------------------------------

NOMBRE_ARCHIVO = 'Registro de inspeccion de calidad - Formimex'
HOJA_BASE = 'BASE DE DATOS'
XLSX_LOCAL = os.path.join('assets', NOMBRE_ARCHIVO + '.xlsx')

# Indice de cada campo dentro de la fila de 'BASE DE DATOS'
# (coincide con el orden en que app.py arma la lista `reporte`)
C = {
    'fecha': 0, 'proveedor': 1, 'material': 2, 'tipo': 3, 'proveedor_nuevo': 4,
    'inspector': 5, 'lote': 6, 'alambre': 7,
    'cant_long': 8, 'cant_trans': 9, 'dim_long': 10, 'dim_trans': 11,
    'perimetro': 12, 'puntas_long': 13, 'puntas_trans': 14,
    'filos_long': 15, 'filos_trans': 16, 'puntos_despegados': 17,
    'prom_diam_long': 26, 'prom_diam_trans': 35,
    'prom_esp_long': 44, 'prom_esp_trans': 53,
    'etiqueta_soldadura': 54, 'resultado_soldadura': 55,
    'pts_despegados_resistencia': 56, 'peso': 57,
}
IDX_DIAM_LONG = list(range(18, 26))   # DL1..DL8
IDX_DIAM_TRANS = list(range(27, 35))  # DT1..DT8
IDX_ESP_LONG = list(range(36, 44))    # EL1..EL8
IDX_ESP_TRANS = list(range(45, 53))   # ET1..ET8

# --------------------------------------------------------------------------
# 2. REGLAS DE NEGOCIO
# --------------------------------------------------------------------------

# Los "proveedores" del reporte rapido se guardan en la columna
# LOTE DE PRODUCCION; la columna PROVEEDOR siempre vale 'FORMIMEX'.
PROVEEDORES = ['NARANJA', 'VERDE', 'ROSA', 'FORMIMEX']
TIPOS_MALLA = ['2x2', '4x4']
TIPOS_ALAMBRE = ['LISO', 'CORRUGADO']

MATERIAL_POR_MALLA = {'2x2': 'MALLA 2X2 8/8', '4x4': 'MALLA 4X4 8/8'}

# Dimension nominal -> (largo_cm, ancho_cm). La base guarda centimetros.
NOMINALES = {
    '3.0 m x 1.8 m': (300.0, 180.0),
    '3.0 m x 2.5 m': (300.0, 250.0),
    '2.7 m x 1.5 m': (270.0, 150.0),
}
DIMENSIONES_POR_MALLA = {
    '2x2': ['3.0 m x 1.8 m'],
    '4x4': ['3.0 m x 1.8 m', '3.0 m x 2.5 m', '2.7 m x 1.5 m'],
}

# Rangos fisicamente posibles: fuera de esto es error de captura, no variacion.
RANGOS = {
    'cant_long': (10, 90), 'cant_trans': (10, 140),
    'prom_diam_long': (3.4, 5.6), 'prom_diam_trans': (3.4, 5.6),
    'prom_esp_long': (35, 140), 'prom_esp_trans': (35, 140),
    'peso': (5, 40),
    'puntas_long': (0, 200), 'puntas_trans': (0, 200),
    'filos_long': (0, 30), 'filos_trans': (0, 30),
    'puntos_despegados': (0, 40), 'pts_despegados_resistencia': (0, 40),
}
RANGO_DIAM = (3.0, 6.0)    # medicion individual de diametro
RANGO_ESP = (30.0, 145.0)  # medicion individual de espaciamiento
# Las dimensiones se validan aparte, despues de reordenar los ejes: una
# fila con longitudinal y transversal invertidos es recuperable, no basura.
RANGO_DIM_LARGO = (200.0, 330.0)
RANGO_DIM_ANCHO = (100.0, 330.0)

MIN_REGISTROS = 5  # minimo para confiar en un nivel de agrupacion
MUESTRA_SUFICIENTE = 15  # a partir de aqui la dispersion del grupo es fiable

# --------------------------------------------------------------------------
# 3. LECTURA DE LA BASE
# --------------------------------------------------------------------------

_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
_NS_REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def _indice_columna(ref):
    letras = re.match(r'([A-Z]+)', ref).group(1)
    n = 0
    for ch in letras:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _leer_xlsx(ruta=XLSX_LOCAL):
    """Lee la hoja BASE DE DATOS del .xlsx sin depender de openpyxl/pandas."""
    z = zipfile.ZipFile(ruta)

    compartidas = []
    try:
        raiz = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in raiz:
            compartidas.append(''.join(t.text or '' for t in si.iter(_NS + 't')))
    except KeyError:
        pass

    # Localizar la hoja por nombre
    libro = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    mapa_rel = {r.get('Id'): r.get('Target') for r in rels}
    destino = None
    for hoja in libro.iter(_NS + 'sheet'):
        if hoja.get('name') == HOJA_BASE:
            destino = mapa_rel.get(hoja.get(_NS_REL + 'id'))
    if not destino:
        return []
    destino = 'xl/' + destino.lstrip('/').split('xl/')[-1]

    raiz = ET.fromstring(z.read(destino))
    filas = []
    for fila in raiz.iter(_NS + 'row'):
        celdas = {}
        for c in fila.iter(_NS + 'c'):
            tipo = c.get('t')
            v = c.find(_NS + 'v')
            inline = c.find(_NS + 'is')
            if v is not None:
                valor = compartidas[int(v.text)] if tipo == 's' else v.text
            elif inline is not None:
                valor = ''.join(t.text or '' for t in inline.iter(_NS + 't'))
            else:
                continue
            celdas[_indice_columna(c.get('r'))] = valor
        if celdas:
            filas.append([celdas.get(i) for i in range(max(celdas) + 1)])
    return filas[1:] if filas else []


def _leer_sheets(client):
    """Lee la hoja BASE DE DATOS en vivo desde Google Sheets."""
    hoja = client.open(NOMBRE_ARCHIVO).worksheet(HOJA_BASE)
    return hoja.get_all_values()[1:]


def cargar_registros(client=None):
    """Devuelve (filas, origen). Intenta Google Sheets y cae al xlsx local."""
    if client is not None:
        try:
            filas = _leer_sheets(client)
            if filas:
                return filas, 'Google Sheets (en vivo)'
        except Exception:
            pass
    try:
        return _leer_xlsx(), 'Archivo local assets/*.xlsx'
    except Exception:
        return [], 'sin datos'


# --------------------------------------------------------------------------
# 4. LIMPIEZA Y CLASIFICACION
# --------------------------------------------------------------------------

def _num(valor):
    try:
        return float(str(valor).replace(',', '').strip())
    except (TypeError, ValueError):
        return None


def _campo(fila, nombre):
    i = C[nombre]
    return fila[i] if i < len(fila) else None


def _numero(fila, nombre):
    return _num(_campo(fila, nombre))


def clasificar_dimension(dim_long, dim_trans):
    """Asigna una medida real a su dimension nominal.

    Corrige el error de captura mas comun: haber invertido longitudinal con
    transversal. Devuelve None si no se parece a ninguna medida estandar.
    """
    if dim_long is None or dim_trans is None:
        return None
    if dim_trans > dim_long:  # ejes invertidos por el capturista
        dim_long, dim_trans = dim_trans, dim_long
    mejor, mejor_dist = None, float('inf')
    for clave, (nl, nt) in NOMINALES.items():
        dist = abs(dim_long - nl) / nl + abs(dim_trans - nt) / nt
        if dist < mejor_dist:
            mejor, mejor_dist = clave, dist
    return mejor if mejor_dist < 0.16 else None


def _normalizar_ejes(fila):
    """Devuelve la fila con longitudinal y transversal en el orden correcto.

    El largo de la pieza siempre es mayor que el ancho, asi que un registro
    donde el transversal supera al longitudinal tiene los ejes invertidos por
    error de captura. Se intercambian las dimensiones y todo lo que va
    emparejado con ellas, en vez de descartar un registro recuperable.
    """
    dl, dt = _numero(fila, 'dim_long'), _numero(fila, 'dim_trans')
    if dl is None or dt is None or dt <= dl:
        return fila
    fila = list(fila)
    for a, b in (('dim_long', 'dim_trans'), ('cant_long', 'cant_trans'),
                 ('puntas_long', 'puntas_trans'), ('filos_long', 'filos_trans'),
                 ('prom_diam_long', 'prom_diam_trans'),
                 ('prom_esp_long', 'prom_esp_trans')):
        fila[C[a]], fila[C[b]] = fila[C[b]], fila[C[a]]
    for ia, ib in ((IDX_DIAM_LONG, IDX_DIAM_TRANS), (IDX_ESP_LONG, IDX_ESP_TRANS)):
        for i, j in zip(ia, ib):
            fila[i], fila[j] = fila[j], fila[i]
    return fila


def _registro_utilizable(fila):
    """Descarta filas incompletas o con valores fisicamente imposibles."""
    if len(fila) < 58:
        return False
    for nombre, (lo, hi) in RANGOS.items():
        v = _numero(fila, nombre)
        if v is None or not (lo <= v <= hi):
            return False
    dl, dt = _numero(fila, 'dim_long'), _numero(fila, 'dim_trans')
    if dl is None or dt is None:
        return False
    if not (RANGO_DIM_LARGO[0] <= dl <= RANGO_DIM_LARGO[1]):
        return False
    if not (RANGO_DIM_ANCHO[0] <= dt <= RANGO_DIM_ANCHO[1]):
        return False
    for i in IDX_DIAM_LONG + IDX_DIAM_TRANS:
        v = _num(fila[i])
        if v is None or not (RANGO_DIAM[0] <= v <= RANGO_DIAM[1]):
            return False
    for i in IDX_ESP_LONG + IDX_ESP_TRANS:
        v = _num(fila[i])
        if v is None or not (RANGO_ESP[0] <= v <= RANGO_ESP[1]):
            return False
    return True


def _sin_outliers(valores):
    """Filtro de rango intercuartil (regla 1.5 * IQR)."""
    v = sorted(x for x in valores if x is not None)
    if len(v) < 5:
        return v
    cuartiles = statistics.quantiles(v, n=4)
    q1, q3 = cuartiles[0], cuartiles[2]
    iqr = q3 - q1
    if iqr == 0:
        return v
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    limpios = [x for x in v if lo <= x <= hi]
    return limpios or v


def _mediana(valores, decimales=2):
    v = _sin_outliers(valores)
    return round(statistics.median(v), decimales) if v else None


def _dispersion_tipica(indice, material, dimension, campo, centro=None):
    """Variacion interna habitual de un campo para ese material y medida.

    Se toma la mediana de las desviaciones *dentro* de cada grupo con
    muestra suficiente. No sirve la desviacion del conjunto entero: esa
    mezcla productos distintos (300 cm contra 305 cm) y describiria la
    diferencia entre proveedores, no cuanto varia la linea al producir.

    Si ninguna medida igual tiene muestra bastante (el caso de 2.7 x 1.5,
    de incorporacion reciente), se traslada la variacion *relativa* del
    material: la tolerancia de corte y el calibre son los mismos aunque
    cambie el tamano de la pieza.
    """
    def recolectar(mismo_tamano):
        datos = []
        for clave, filas in indice.items():
            if clave[1] != material:
                continue
            if mismo_tamano and clave[2] != dimension:
                continue
            v = _sin_outliers([_numero(f, campo)
                               for f in _configuracion_dominante(filas)])
            if len(v) >= MUESTRA_SUFICIENTE:
                datos.append((statistics.stdev(v), statistics.median(v)))
        return datos

    datos = recolectar(True)
    if datos:
        return statistics.median(d for d, _ in datos)
    datos = recolectar(False)
    if datos and centro:
        relativa = statistics.median(d / m for d, m in datos if m)
        return abs(centro) * relativa
    return 0.0


def _estadistica(valores, desv_referencia=None):
    """Centro y dispersion reales de un campo dentro del grupo.

    Devuelve (mediana, desviacion, minimo, maximo) sobre los valores ya
    limpios de atipicos. El minimo y el maximo son medidas que realmente se
    tomaron, y sirven de tope para que lo generado nunca salga del rango
    que el proceso ha producido de verdad.

    Con pocos registros la dispersion observada subestima la del proceso:
    tres piezas casi identicas no prueban que la linea no varie, solo que
    no hay muestra. En ese caso se conserva el centro del grupo y se adopta
    la variacion interna habitual de ese material y medida.
    """
    v = _sin_outliers(valores)
    if not v:
        return None
    centro = statistics.median(v)
    desviacion = statistics.stdev(v) if len(v) >= 2 else 0.0
    minimo, maximo = min(v), max(v)

    if (desv_referencia and len(v) < MUESTRA_SUFICIENTE
            and desv_referencia > desviacion):
        desviacion = desv_referencia
        minimo = min(minimo, centro - 2 * desv_referencia)
        maximo = max(maximo, centro + 2 * desv_referencia)
    return centro, desviacion, minimo, maximo


def _muestrear(rng, est, decimales):
    """Valor dentro de la dispersion historica del grupo.

    Sin generador devuelve el centro (la tendencia pura). Con generador
    toma una normal centrada en la mediana con la desviacion observada,
    truncada al rango real: el reporte varia en cada emision pero nunca se
    sale de lo que ese proveedor ha entregado historicamente.
    """
    if est is None:
        return None
    centro, desviacion, minimo, maximo = est
    if rng is None or desviacion <= 0:
        return round(centro, decimales)
    # Los topes se cierran hacia adentro para que el redondeo final no
    # empuje el valor fuera del rango realmente observado.
    paso = 10.0 ** -decimales
    piso = math.ceil(minimo / paso - 1e-9) * paso
    techo = math.floor(maximo / paso + 1e-9) * paso
    if piso > techo:
        return round(centro, decimales)
    for _ in range(12):
        v = round(rng.gauss(centro, desviacion), decimales)
        if piso <= v <= techo:
            return v
    return round(min(max(round(rng.gauss(centro, desviacion), decimales), piso), techo), decimales)


def _moda(valores):
    v = _sin_outliers(valores)
    return int(Counter(v).most_common(1)[0][0]) if v else None


def _moda_texto(valores, respaldo=None):
    v = [x for x in valores if x not in (None, '')]
    return Counter(v).most_common(1)[0][0] if v else respaldo


def _moda_par(grupo, campo_a, campo_b):
    """Moda conjunta de dos campos acoplados.

    Tomar la moda de cada campo por separado puede devolver una combinacion
    que nunca existio: si un grupo mezcla dos productos (por ejemplo 37/61 y
    34/55 alambres), el resultado seria 37/55. Se elige el par completo mas
    frecuente para conservar la coherencia geometrica del registro.
    """
    pares = []
    for fila in grupo:
        a, b = _numero(fila, campo_a), _numero(fila, campo_b)
        if a is not None and b is not None:
            pares.append((int(a), int(b)))
    if not pares:
        return None, None
    return Counter(pares).most_common(1)[0][0]


def _configuracion_dominante(grupo):
    """Reduce el grupo a los registros que comparten el armado mas frecuente.

    Un mismo proveedor y dimension pueden agrupar dos armados distintos
    (por ejemplo 37x61 y 34x55 alambres). Calcular medianas sobre la mezcla
    produce una pieza que no corresponde a ninguno de los dos. Se conserva
    el armado dominante siempre que respalde una parte significativa del
    grupo; si no, se deja el grupo completo.
    """
    par = _moda_par(grupo, 'cant_long', 'cant_trans')
    if par == (None, None):
        return grupo
    coherentes = [f for f in grupo
                  if (_numero(f, 'cant_long'), _numero(f, 'cant_trans')) == par]
    if len(coherentes) >= 3 and len(coherentes) >= 0.25 * len(grupo):
        return coherentes
    return grupo


# --------------------------------------------------------------------------
# 5. AGRUPACION CON RESPALDO JERARQUICO
# --------------------------------------------------------------------------

def construir_indice(filas):
    """Agrupa los registros limpios por (lote, material, dimension, alambre)."""
    indice = {}
    descartados = 0
    for fila in filas:
        # Se corrigen los ejes invertidos antes de juzgar la fila: de lo
        # contrario un registro recuperable se descartaria por rango.
        fila = _normalizar_ejes(fila)
        if not _registro_utilizable(fila):
            descartados += 1
            continue
        dim = clasificar_dimension(_numero(fila, 'dim_long'),
                                   _numero(fila, 'dim_trans'))
        if dim is None:
            descartados += 1
            continue
        clave = (_campo(fila, 'lote'), _campo(fila, 'material'), dim,
                 _campo(fila, 'alambre'))
        indice.setdefault(clave, []).append(fila)
    return indice, descartados


def _candidatos(indice, lote, material, dim, alambre):
    """Cadena de respaldo: de lo mas especifico a lo mas general.

    Los primeros cuatro niveles conservan siempre la dimension solicitada.
    Renunciar a la dimension (ultimo nivel) solo ocurre si no existe ni un
    solo registro historico de esa medida, y obliga a corregir la geometria.
    """
    niveles = [
        ('%s + %s + %s + %s' % (lote, material, dim, alambre),
         lambda k: k == (lote, material, dim, alambre)),
        ('%s + %s + %s (cualquier proveedor)' % (material, dim, alambre),
         lambda k: k[1] == material and k[2] == dim and k[3] == alambre),
        ('%s + %s + %s (cualquier alambre)' % (lote, material, dim),
         lambda k: k[0] == lote and k[1] == material and k[2] == dim),
        ('%s + %s (cualquier proveedor y alambre)' % (material, dim),
         lambda k: k[1] == material and k[2] == dim),
    ]
    mejor_parcial = None
    for etiqueta, prueba in niveles:
        grupo = [f for k, fs in indice.items() if prueba(k) for f in fs]
        if len(grupo) >= MIN_REGISTROS:
            return grupo, etiqueta, True
        if grupo and (mejor_parcial is None or len(grupo) > len(mejor_parcial[0])):
            mejor_parcial = (grupo, etiqueta + ' (muestra escasa)', True)
    if mejor_parcial:
        return mejor_parcial

    # Sin historial de esa dimension: se toma la referencia del material y la
    # geometria se reconstruye a partir de la medida nominal.
    grupo = [f for k, fs in indice.items() if k[1] == material for f in fs]
    return grupo, '%s (sin historial de %s, geometria calculada)' % (material, dim), False


def _ajustar_geometria(perfil, dimension):
    """Reconstruye dimension, conteo de alambres y peso para la medida pedida.

    Se usa cuando el respaldo historico proviene de otra dimension: el
    espaciamiento y el diametro si son transferibles, pero el tamano de la
    pieza y su peso no.
    """
    nl, nt = NOMINALES[dimension]
    largo_prev = perfil.get('dim_long') or nl
    ancho_prev = perfil.get('dim_trans') or nt
    esp_l = perfil.get('prom_esp_long') or 0
    esp_t = perfil.get('prom_esp_trans') or 0

    # Los alambres longitudinales se reparten a lo ancho y viceversa.
    if esp_l:
        perfil['cant_long'] = int(round(nt * 10 / esp_l)) + 1
    if esp_t:
        perfil['cant_trans'] = int(round(nl * 10 / esp_t)) + 1

    # El peso sigue la longitud total de alambre, no el area.
    metros_prev = ((perfil.get('_cant_long_prev') or 0) * largo_prev
                   + (perfil.get('_cant_trans_prev') or 0) * ancho_prev)
    metros_nuevo = perfil['cant_long'] * nl + perfil['cant_trans'] * nt
    if metros_prev and perfil.get('peso'):
        perfil['peso'] = round(perfil['peso'] * metros_nuevo / metros_prev, 2)

    perfil['dim_long'], perfil['dim_trans'] = nl, nt
    # Sin evidencia de la pieza real, no se presumen defectos de perimetro.
    perfil['puntas_long'] = perfil['puntas_trans'] = 0
    return perfil


# --------------------------------------------------------------------------
# 6. PREDICCION DEL PERFIL
# --------------------------------------------------------------------------

def _medoide(grupo, centro):
    """Registro real mas cercano al centro robusto del grupo.

    Se usa como plantilla de las 32 mediciones individuales para que
    conserven una dispersion realista en vez de 8 numeros identicos.
    """
    campos = ['prom_diam_long', 'prom_diam_trans',
              'prom_esp_long', 'prom_esp_trans']
    mejor, mejor_dist = None, float('inf')
    for fila in grupo:
        dist = 0.0
        for campo in campos:
            ref = centro.get(campo)
            v = _numero(fila, campo)
            if ref and v:
                dist += abs(v - ref) / ref
        if dist < mejor_dist:
            mejor, mejor_dist = fila, dist
    return mejor


def _serie(fila, indices, objetivo, decimales, rng, ruido):
    """Toma las 8 lecturas de la plantilla y las recentra al valor esperado."""
    valores = [_num(fila[i]) for i in indices]
    if objetivo is not None and all(v is not None for v in valores):
        desfase = objetivo - statistics.fmean(valores)
        valores = [v + desfase for v in valores]
    if rng is not None and ruido:
        valores = [v + rng.gauss(0, ruido) for v in valores]
    return [round(v, decimales) for v in valores]


def predecir_perfil(indice, lote, tipo_malla, dimension, alambre,
                    semilla=None, variar=False):
    """Calcula el perfil tipico esperado para una combinacion.

    Devuelve un diccionario con todos los campos del reporte mas metadatos
    (`_n`, `_n_nivel`, `_nivel`) que indican cuanta evidencia lo respalda.
    """
    material = MATERIAL_POR_MALLA[tipo_malla]
    grupo, nivel, dim_confiable = _candidatos(indice, lote, material,
                                              dimension, alambre)
    if not grupo:
        return None
    total_nivel = len(grupo)
    grupo = _configuracion_dominante(grupo)

    # Un generador propio por reporte: con `variar` activo cada emision cae
    # en un punto distinto de la dispersion historica del grupo.
    rng = random.Random(semilla) if variar else None

    def med(nombre, dec=2):
        """Valor muestreado dentro de la tendencia de ese campo."""
        valores = [_numero(f, nombre) for f in grupo]
        referencia = None
        if len(grupo) < MUESTRA_SUFICIENTE:
            limpios = _sin_outliers(valores)
            centro = statistics.median(limpios) if limpios else None
            referencia = _dispersion_tipica(indice, material, dimension,
                                            nombre, centro)
        return _muestrear(rng, _estadistica(valores, referencia), dec)

    def mod(nombre):
        return _moda([_numero(f, nombre) for f in grupo])

    perfil = {
        '_n': len(grupo),
        '_n_nivel': total_nivel,
        '_nivel': nivel,
        'tipo': _moda_texto([_campo(f, 'tipo') for f in grupo], 'MP'),
        'proveedor_nuevo': _moda_texto(
            [_campo(f, 'proveedor_nuevo') for f in grupo], 'NO'),
        'perimetro': _moda_texto(
            [_campo(f, 'perimetro') for f in grupo], 'COMPLETO'),
        'resultado_soldadura': _moda_texto(
            [_campo(f, 'resultado_soldadura') for f in grupo],
            'LOS PUNTOS SI RESISTEN'),
        'dim_long': med('dim_long', 1),
        'dim_trans': med('dim_trans', 1),
        'puntos_despegados': mod('puntos_despegados'),
        'pts_despegados_resistencia': mod('pts_despegados_resistencia'),
        'peso': med('peso'),
        'prom_diam_long': med('prom_diam_long'),
        'prom_diam_trans': med('prom_diam_trans'),
        'prom_esp_long': med('prom_esp_long'),
        'prom_esp_trans': med('prom_esp_trans'),
    }

    # Campos acoplados entre si: se toman como par para no inventar mezclas.
    perfil['cant_long'], perfil['cant_trans'] = _moda_par(
        grupo, 'cant_long', 'cant_trans')
    perfil['puntas_long'], perfil['puntas_trans'] = _moda_par(
        grupo, 'puntas_long', 'puntas_trans')
    perfil['filos_long'], perfil['filos_trans'] = _moda_par(
        grupo, 'filos_long', 'filos_trans')

    if not dim_confiable:
        perfil['_cant_long_prev'] = perfil['cant_long']
        perfil['_cant_trans_prev'] = perfil['cant_trans']
        _ajustar_geometria(perfil, dimension)
        perfil.pop('_cant_long_prev')
        perfil.pop('_cant_trans_prev')

    # Ningun campo entero puede quedar vacio: el formulario los requiere.
    for campo in ('cant_long', 'cant_trans', 'puntas_long', 'puntas_trans',
                  'filos_long', 'filos_trans', 'puntos_despegados',
                  'pts_despegados_resistencia'):
        if perfil.get(campo) is None:
            perfil[campo] = 1 if campo.startswith('cant_') else 0

    # La plantilla aporta la forma de las 8 lecturas (su dispersion interna).
    # Sin variacion se usa el registro mas representativo; con variacion, una
    # inspeccion real cualquiera del grupo, distinta en cada emision.
    plantilla = rng.choice(grupo) if rng is not None else _medoide(grupo, perfil)
    perfil['diam_long'] = _serie(plantilla, IDX_DIAM_LONG,
                                 perfil['prom_diam_long'], 2, rng,
                                 0.02 if variar else 0)
    perfil['diam_trans'] = _serie(plantilla, IDX_DIAM_TRANS,
                                  perfil['prom_diam_trans'], 2, rng,
                                  0.02 if variar else 0)
    perfil['esp_long'] = _serie(plantilla, IDX_ESP_LONG,
                                perfil['prom_esp_long'], 2, rng,
                                0.4 if variar else 0)
    perfil['esp_trans'] = _serie(plantilla, IDX_ESP_TRANS,
                                 perfil['prom_esp_trans'], 2, rng,
                                 0.4 if variar else 0)

    # Los promedios siempre se recalculan a partir de las lecturas mostradas.
    perfil['prom_diam_long'] = round(statistics.fmean(perfil['diam_long']), 2)
    perfil['prom_diam_trans'] = round(statistics.fmean(perfil['diam_trans']), 2)
    perfil['prom_esp_long'] = round(statistics.fmean(perfil['esp_long']), 2)
    perfil['prom_esp_trans'] = round(statistics.fmean(perfil['esp_trans']), 2)
    return perfil
