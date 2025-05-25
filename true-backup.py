import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import sys # Added for sys.exit
from requests.auth import HTTPBasicAuth # Added for Basic Auth


# Cargar variables de entorno
load_dotenv()

TRUENAS_URL = os.getenv('TRUENAS_URL')
API_KEY = os.getenv('API_KEY')
TRUENAS_USER = os.getenv('TRUENAS_USER')
TRUENAS_PASS = os.getenv('TRUENAS_PASS')
AUTH_METHOD = os.getenv('AUTH_METHOD', 'token').lower() # Default to 'token' and normalize to lowercase

# Validate TRUENAS_URL
if not TRUENAS_URL:
    print("Error: TRUENAS_URL no está configurada en el archivo .env.")
    sys.exit(1)

try:
    # Obtener la fecha y hora actual para el nombre del archivo
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"truebackup_{now}.db"

    request_args = {
        "params": {
            "secretseed": True,
            "root_authorized_keys": True
        },
        "verify": False
    }

    # Configurar autenticación
    if AUTH_METHOD == 'basic':
        print("Usando autenticación básica.")
        if not TRUENAS_USER or not TRUENAS_PASS:
            print("Error: TRUENAS_USER y TRUENAS_PASS son necesarios para la autenticación básica.")
            sys.exit(1)
        request_args["auth"] = HTTPBasicAuth(TRUENAS_USER, TRUENAS_PASS)
    elif AUTH_METHOD == 'token':
        print("Usando autenticación por token.")
        if not API_KEY:
            print("Error: API_KEY es necesario para la autenticación por token.")
            sys.exit(1)
        request_args["headers"] = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json" # Kept as in original for token auth
        }
    else:
        print(f"Error: Método de autenticación '{AUTH_METHOD}' no soportado. Use 'basic' o 'token'.")
        sys.exit(1)
    
    # Hacer la solicitud para crear el backup
    print(f"Intentando descargar backup desde: {TRUENAS_URL}")
    response = requests.get(
        TRUENAS_URL,
        **request_args
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
