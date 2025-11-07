# Control de Calidad Digital - Malla Electrosoldada - v2

**Autor:** _Samuel Contreras Cruz_  
Supervisor de Calidad y Desarrollador del Sistema  
**Empresa:** Formimex – Área de Calidad (Malla Electrosoldada)

---

## 📌 Descripción del Proyecto

Este proyecto consiste en una aplicación web para digitalizar y automatizar el proceso de inspección de **mallas electrosoldadas** en Formimex.  
Previo al desarrollo, los reportes se llenaban manualmente en papel, provocando:

- Errores en cálculos
- Tiempos excesivos de captura
- Problemas de legibilidad
- Dificultad para consulta histórica

La aplicación:
✅ Genera reportes PDF automáticamente  
✅ Almacena los datos en una base de datos centralizada  
✅ Organiza documentos por fecha y por inspector  
✅ Mantiene el formato oficial de la empresa  

Es el primer paso hacia la transformación digital del sistema de calidad en planta.

---

## 🎯 Objetivos

- Automatizar procesos de inspección
- Reducir errores humanos
- Mejorar eficiencia operativa
- Facilitar auditorías y trazabilidad de información
- Escalar a otras áreas productivas en Formimex

---

## 🧪 Parámetros de Inspección

El sistema permite registrar:

- Tipo de alambre
- Cantidad de alambres
- Puntas y filos
- Puntos de soldadura despegados
- Diámetro del alambre
- Espaciamiento de cuadros
- Resistencia de soldadura (25 Nm y 30 Nm)
- Peso de la malla

📌 Inspector por turno: **2 supervisores en total**  
📌 Inspecciones diarias: **18 – 24**  
📉 Tiempo por reporte: **30 min ➜ 15 min** (50% mejora)

---

## 🛠 Tecnologías Utilizadas

| Área | Tecnología |
|------|------------|
| Lenguaje | Python |
| Framework Web | Streamlit |
| Integración con Google Sheets | gspread |
| Generación de PDFs | Autocrat (Google Workspace) |
| Gestión documental | Google Drive (carpetas automáticas por día) |
| Plantilla interna | FO-CCA-04 – Inspección de Mallas Electrosoldadas |

---

## 🌐 Accesos

| Recurso | Enlace |
|--------|--------|
| **Aplicación Web** | https://formimex-inspeccion-de-calidad.streamlit.app/ |
| **Repositorio** | https://github.com/contrerascs/Formimex |
| **Base de Datos interna (Google Sheets)** | Acceso restringido a personal autorizado |

---

## 📂 Estructura del Proyecto

/src
├─ app.py # Aplicación en Streamlit
├─ utils/ # Funciones auxiliares
├─ services/ # Conexiones con Google Sheets y Drive
/template
└─ FO-CCA-04.xlsx # Formato oficial de inspección
/docs
└─ Capturas/ # (Pendiente por agregar)


## ✅ Funcionalidades

- Registro digital de inspecciones de malla electrosoldada
- Cálculos automáticos para evitar errores humanos
- Generación de PDF con formato corporativo
- Nombre estándar por documento:

- Base de datos actualizada en tiempo real
- Organización automática por fecha en Drive

---

## 📌 Alcance Actual

- Usado únicamente por Supervisores de calidad del área de Malla
- Sistema estable en operación
- Aún con posibilidad de captura manual en la base de datos

---

## 🚧 Roadmap

- ✅ Automatización de carpetas por día
- 🔄 Automatización por mes (en desarrollo)
- 🛡 Inicio de sesión y roles de usuario
- 📈 Dashboard de indicadores de calidad
- 🚀 Expansión a más áreas de producción

---

## 📊 Beneficios para Formimex

| Antes (manual) | Ahora (digital) |
|----------------|----------------|
| Cálculos manuales y errores | Cálculos automáticos y exactos |
| Documentos difíciles de leer | PDFs legibles y estandarizados |
| Trazabilidad limitada | Historial accesible y organizado |
| 30 min por inspección | 15 min por inspección |
| Captura manual en sistemas | Base de datos automática |

💡 Mayor productividad + menos errores + mejor control

---

## 📥 Capturas del Sistema
_(Pendiente por agregar)_

---

## 🧑‍💼 Contacto del Desarrollador

**Samuel Contreras Cruz**  
Supervisor de Calidad & Software Developer  
📩 Email: _(Puedes agregarlo si deseas que esté público)_

---

> Este proyecto forma parte del proceso de digitalización del área de calidad en Formimex y continuará evolucionando para ofrecer mayor valor a la operación.

---
