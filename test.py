import gspread
from google.oauth2.service_account import Credentials

# Define los alcances necesarios para interactuar con Sheets y Drive
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive']

# Carga las credenciales desde el archivo JSON
credentials = Credentials.from_service_account_file('keys/keys.json', scopes=scopes)

# Crea un cliente autorizado de gspread
client = gspread.authorize(credentials)

#Agregamos datos a tabla de Google Sheets
sheet = client.open('Inspeccion de calidad - Formimex - v2').sheet1
#sheet.update('A1', [[1, 2, 3], [4, 5, 6]])
sheet.append_row([1, 2, 3, 4, 5, 6])