import requests
from datetime import datetime
from dotenv import load_dotenv
import os


# Cargar variables de entorno
load_dotenv()

TRUENAS_URL = os.getenv('TRUENAS_URL')
API_KEY = os.getenv('API_KEY')

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

try:
    # Obtener la fecha y hora actual para el nombre del archivo
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"truebackup_{now}.db"
    
    # Hacer la solicitud para crear el backup
    response = requests.get(
        TRUENAS_URL,
        headers=headers,
        params={
            "secretseed": True,
            "root_authorized_keys": True
        },
        verify=False
    )
    
    response.raise_for_status()
    
    # Guardar el archivo directamente ya que el endpoint devuelve el archivo
    with open(filename, "wb") as f:
        f.write(response.content)
    
    print(f"Backup descargado correctamente como {filename}")
    
except requests.exceptions.HTTPError as e:
    print(f"Error HTTP {e.response.status_code}: {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")
