import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import sys # Added for sys.exit
from requests.auth import HTTPBasicAuth # Added for Basic Auth
import boto3 # Added for S3 upload
from botocore.exceptions import NoCredentialsError, ClientError # Added for S3 error handling


# Cargar variables de entorno
load_dotenv()

# TrueNAS Configuration
TRUENAS_URL = os.getenv('TRUENAS_URL')
API_KEY = os.getenv('API_KEY')
TRUENAS_USER = os.getenv('TRUENAS_USER')
TRUENAS_PASS = os.getenv('TRUENAS_PASS')
AUTH_METHOD = os.getenv('AUTH_METHOD', 'token').lower() # Default to 'token' and normalize to lowercase

# S3 Configuration
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_REGION = os.getenv('S3_REGION') # Optional
DELETE_LOCAL_BACKUP_AFTER_UPLOAD = os.getenv('DELETE_LOCAL_BACKUP_AFTER_UPLOAD', 'false').lower()


def upload_to_s3(local_file_path, s3_object_name, endpoint_url, access_key_id, secret_access_key, bucket_name, region_name=None, delete_local_after_upload='false'):
    """
    Sube un archivo a un servicio de almacenamiento compatible con S3.

    Args:
        local_file_path (str): Ruta al archivo local a subir.
        s3_object_name (str): Nombre del objeto en S3 (nombre del archivo en el bucket).
        endpoint_url (str): URL del endpoint S3.
        access_key_id (str): Access Key ID de S3.
        secret_access_key (str): Secret Access Key de S3.
        bucket_name (str): Nombre del bucket S3.
        region_name (str, optional): Región S3. Defaults to None.
        delete_local_after_upload (str, optional): 'true' o 'yes' para eliminar el archivo local después de subirlo. Defaults to 'false'.

    Returns:
        bool: True si la subida fue exitosa, False en caso contrario.
    """
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name
        )
        s3_client.upload_file(local_file_path, bucket_name, s3_object_name)
        print(f"Backup {s3_object_name} subido correctamente al bucket {bucket_name}.")

        if delete_local_after_upload in ['true', 'yes', '1']:
            try:
                os.remove(local_file_path)
                print(f"Archivo de backup local {local_file_path} eliminado correctamente.")
            except OSError as e:
                print(f"Error al eliminar el archivo de backup local {local_file_path}: {e}")
        else:
            print(f"Archivo de backup local {local_file_path} conservado.")
        return True
    except FileNotFoundError:
        print(f"Error: El archivo de backup local {local_file_path} no fue encontrado para la subida a S3.")
    except NoCredentialsError:
        print("Error: Credenciales S3 no disponibles o incorrectas.")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "NoSuchBucket":
            print(f"Error S3: El bucket '{bucket_name}' no existe.")
        elif error_code == "InvalidAccessKeyId":
            print(f"Error S3: AWS Access Key ID inválido.")
        elif error_code == "SignatureDoesNotMatch":
            print(f"Error S3: AWS Secret Access Key es incorrecto.")
        elif "AccessDenied" in str(e):
             print(f"Error S3: Acceso denegado. Verifica los permisos para el bucket '{bucket_name}'.")
        else:
            print(f"Error de cliente S3: {e}")
    except Exception as e:
        print(f"Error inesperado durante la subida a S3: {e}")
    
    # Si la subida falla, asegurarse de que el archivo local no se elimine por error si el flag estaba puesto
    print(f"Archivo de backup local {local_file_path} conservado debido a un error en la subida a S3.")
    return False

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

    # Intentar subir a S3 si la configuración está presente
    if S3_ENDPOINT_URL and S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY and S3_BUCKET_NAME:
        print(f"Intentando subir {filename} a S3 bucket {S3_BUCKET_NAME} en {S3_ENDPOINT_URL}...")
        upload_successful = upload_to_s3(
            local_file_path=filename,
            s3_object_name=filename,
            endpoint_url=S3_ENDPOINT_URL,
            access_key_id=S3_ACCESS_KEY_ID,
            secret_access_key=S3_SECRET_ACCESS_KEY,
            bucket_name=S3_BUCKET_NAME,
            region_name=S3_REGION,
            delete_local_after_upload=DELETE_LOCAL_BACKUP_AFTER_UPLOAD
        )
        # La función upload_to_s3 ya imprime mensajes sobre el resultado y la eliminación.
    else:
        print("Configuración S3 no proporcionada o incompleta. Saltando subida a S3.")
        print(f"Archivo de backup local {filename} conservado.")

except requests.exceptions.HTTPError as e:
    print(f"Error HTTP {e.response.status_code}: {e.response.text}")
    # Si la descarga falla, el archivo local 'filename' podría no existir o estar incompleto.
    # No hay necesidad de intentar eliminarlo aquí, ya que la subida a S3 no ocurrirá.
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")
