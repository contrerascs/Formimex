# 🧾 Generador de Reportes de Inspección – FORMIMEX

Esta aplicación web fue desarrollada para **FORMIMEX**, con el objetivo de **generar reportes de inspección de calidad de mallas electrosoldadas** de manera sencilla y automatizada.  
La aplicación está construida con **Streamlit** y se conecta a **Google Sheets** para almacenar y administrar la información registrada.

---

## 🚀 Características principales

- Registro digital de reportes de inspección.  
- Carga automática de datos en hojas de cálculo de Google.  
- Interfaz intuitiva y fácil de usar.  
- Campos con control de fecha, hora y validación básica.  

---

## 🧩 Librerías utilizadas

| Librería | Descripción |
|-----------|-------------|
| **streamlit** | Crea la interfaz web interactiva. |
| **datetime** | Maneja fechas y horas para los reportes. |
| **gspread** | Permite la conexión y escritura en Google Sheets. |
| **google.oauth2.service_account** | Gestiona la autenticación segura mediante credenciales JSON. |

---

## ⚙️ Configuración

1. Clona este repositorio:
   ```bash
   git clone https://github.com/contrerascs/Formimex.git
   cd Formimex
