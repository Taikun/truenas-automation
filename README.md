# TrueNAS Client

Un conjunto de scripts en Python para interactuar con la API de TrueNAS.

## Scripts disponibles

- `check-pools-basic-auth.py`: Muestra el estado de los pools usando autenticación básica.
- `check-pools-token.py`: Muestra el estado de los pools usando token de autenticación.
- `true-backup.py`: Descarga un backup de la configuración del sistema TrueNAS. Soporta autenticación básica y por token, y opcionalmente sube el backup a un servicio S3 compatible.

## Requisitos

- Python 3.9+
- Las dependencias especificadas en `requirements.txt`

## Instalación

1. Clona el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd truenas_client
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las credenciales:
Crea un archivo `.env` con las siguientes variables:
```
TRUENAS_URL=https://tu-servidor-truenas/api/v2.0/
# Para check-pools-token.py y true-backup.py (si AUTH_METHOD=token)
API_KEY=tu-token-de-api 
# Para check-pools-basic-auth.py y true-backup.py (si AUTH_METHOD=basic)
TRUENAS_USER=tu-usuario-truenas
TRUENAS_PASS=tu-contraseña-truenas
# Específico para true-backup.py
AUTH_METHOD=token 
```

### Configuración Detallada para `true-backup.py`

El script `true-backup.py` permite descargar un backup de la configuración de TrueNAS. Es crucial configurar correctamente las variables de entorno para su funcionamiento.

**Propósito**: Realizar una copia de seguridad de la configuración del sistema TrueNAS, incluyendo la semilla secreta y las claves autorizadas de root.

**Métodos de Autenticación**:
El script soporta dos métodos de autenticación, configurables mediante la variable de entorno `AUTH_METHOD`:
- `token` (por defecto): Utiliza un API Key para la autenticación.
- `basic`: Utiliza un nombre de usuario y contraseña.

Si `AUTH_METHOD` no se especifica, el script usará `token` como método por defecto.

**Variables de Entorno para `true-backup.py`**:

- `TRUENAS_URL`: La URL completa de tu instancia de TrueNAS, incluyendo el protocolo y el path a la API si es necesario para el endpoint de backup. Ejemplo: `http://truenas.local/api/v2.0/system/config/save` (Nota: `true-backup.py` usa esta URL directamente para el GET request del backup). Para el script `true-backup.py`, esta URL debe ser el endpoint exacto para descargar el archivo de configuración, por ejemplo, `http://<truenas_ip_o_dominio>/api/v2.0/system/config/save`.
- `AUTH_METHOD`: Define el método de autenticación. Puede ser `token` o `basic`. Si no se define, se usará `token`.
- `API_KEY`: Tu API Key de TrueNAS. Necesaria si `AUTH_METHOD` es `token` (o si no está definida).
- `TRUENAS_USER`: Tu nombre de usuario de TrueNAS. Necesario si `AUTH_METHOD` es `basic`.
- `TRUENAS_PASS`: Tu contraseña de TrueNAS. Necesaria si `AUTH_METHOD` es `basic`.

**Variables de Entorno Adicionales para S3 (Opcional)**:
Si deseas subir el backup a un almacenamiento compatible con S3, configura las siguientes variables. Si no se configuran, el script solo guardará el backup localmente.

- `S3_ENDPOINT_URL`: La URL del endpoint de tu servicio S3 (ej. `https://s3.tuproveedor.com` o `http://ip-minio:9000` para MinIO).
- `S3_ACCESS_KEY_ID`: Tu Access Key ID de S3.
- `S3_SECRET_ACCESS_KEY`: Tu Secret Access Key de S3.
- `S3_BUCKET_NAME`: El nombre del bucket S3 donde se guardará el backup.
- `S3_REGION`: La región S3 (ej. `us-east-1`). Opcional dependiendo de la configuración de tu proveedor S3.
- `DELETE_LOCAL_BACKUP_AFTER_UPLOAD`: Define si el archivo de backup local debe eliminarse después de una subida exitosa a S3. Valores como `true`, `yes`, o `1` activarán la eliminación. Cualquier otro valor (o si la variable no está definida) conservará el archivo local (comportamiento por defecto: `false`).

**Ejemplos de configuración del archivo `.env` para `true-backup.py`**:

1.  **Usando Autenticación por Token (`AUTH_METHOD=token` o no especificado)**:
    ```dotenv
    TRUENAS_URL=http://<truenas_ip_o_dominio>/api/v2.0/system/config/save
    AUTH_METHOD=token
    API_KEY=abcdef1234567890abcdef1234567890abcdef1234567890
    # TRUENAS_USER y TRUENAS_PASS pueden omitirse o dejarse en blanco
    ```

2.  **Usando Autenticación Básica (`AUTH_METHOD=basic`)**:
    ```dotenv
    TRUENAS_URL=http://<truenas_ip_o_dominio>/api/v2.0/system/config/save
    AUTH_METHOD=basic
    TRUENAS_USER=miusuario
    TRUENAS_PASS=micontraseña
    # API_KEY puede omitirse o dejarse en blanco
    ```

3.  **Usando Autenticación por Token y Subida a S3 (con eliminación del backup local)**:
    ```dotenv
    TRUENAS_URL=http://<truenas_ip_o_dominio>/api/v2.0/system/config/save
    AUTH_METHOD=token
    API_KEY=abcdef1234567890abcdef1234567890abcdef1234567890
    
    S3_ENDPOINT_URL=http://minio.local:9000
    S3_ACCESS_KEY_ID=tu_access_key_id_s3
    S3_SECRET_ACCESS_KEY=tu_secret_access_key_s3
    S3_BUCKET_NAME=truenas-backups
    S3_REGION=us-east-1 # Opcional, ajustar según sea necesario
    DELETE_LOCAL_BACKUP_AFTER_UPLOAD=true
    ```

**Nota sobre `TRUENAS_URL` para `true-backup.py`**: A diferencia de otros scripts que pueden usar una URL base de API, `true-backup.py` espera que `TRUENAS_URL` sea el endpoint específico desde el cual se descarga el archivo de configuración (backup). El script anexa los parámetros `secretseed=true` y `root_authorized_keys=true` a esta URL.

### Manual Testing for `true-backup.py`

Esta sección describe cómo probar manualmente el script `true-backup.py` con ambos métodos de autenticación.

**Prerrequisitos**:
- Una instancia de TrueNAS accesible desde la máquina donde ejecutarás el script.
- Credenciales válidas (API Key o usuario/contraseña) para la instancia de TrueNAS.
- El endpoint correcto para `TRUENAS_URL` que permite la descarga del backup (e.g., `http://<tu-truenas>/api/v2.0/system/config/save`).

**1. Test con Autenticación por Token**:

*   **Configuración del archivo `.env`**:
    Asegúrate de que tu archivo `.env` esté configurado de la siguiente manera:
    ```dotenv
    TRUENAS_URL=http://<tu-truenas>/api/v2.0/system/config/save
    AUTH_METHOD=token  # O puedes omitir esta línea, ya que 'token' es el valor por defecto
    API_KEY=tu_api_key_valida
    # TRUENAS_USER y TRUENAS_PASS no son necesarios para este método y pueden omitirse.
    ```
*   **Ejecución del Script**:
    Abre una terminal en el directorio del proyecto y ejecuta:
    ```bash
    python true-backup.py
    ```
*   **Verificación de Éxito**:
    - Deberías ver un mensaje como: `Usando autenticación por token.` seguido de `Intentando descargar backup desde: <tu_url>`.
    - Luego, un mensaje de éxito: `Backup descargado correctamente como truebackup_YYYYMMDD_HHMMSS.db`.
    - Verifica que se haya creado un archivo `.db` con la fecha y hora actuales en el directorio.
*   **Verificación de Fallo**:
    - Si `API_KEY` es incorrecta o falta, verás: `Error: API_KEY es necesario para la autenticación por token.`
    - Si `TRUENAS_URL` es incorrecta o inaccesible, verás errores HTTP o de conexión, por ejemplo: `Error HTTP 401: Unauthorized ...` o `Error de conexión: ...`.

**2. Test con Autenticación Básica**:

*   **Configuración del archivo `.env`**:
    Asegúrate de que tu archivo `.env` esté configurado de la siguiente manera:
    ```dotenv
    TRUENAS_URL=http://<tu-truenas>/api/v2.0/system/config/save
    AUTH_METHOD=basic
    TRUENAS_USER=tu_usuario_valido
    TRUENAS_PASS=tu_contraseña_valida
    # API_KEY no es necesario para este método y puede omitirse.
    ```
*   **Ejecución del Script**:
    Abre una terminal en el directorio del proyecto y ejecuta:
    ```bash
    python true-backup.py
    ```
*   **Verificación de Éxito**:
    - Deberías ver un mensaje como: `Usando autenticación básica.` seguido de `Intentando descargar backup desde: <tu_url>`.
    - Luego, un mensaje de éxito: `Backup descargado correctamente como truebackup_YYYYMMDD_HHMMSS.db`.
    - Verifica que se haya creado un archivo `.db` con la fecha y hora actuales.
*   **Verificación de Fallo**:
    - Si `TRUENAS_USER` o `TRUENAS_PASS` son incorrectos o faltan, verás: `Error: TRUENAS_USER y TRUENAS_PASS son necesarios para la autenticación básica.`
    - Si las credenciales son inválidas, es probable que recibas un error HTTP `401 Unauthorized`.
    - Si `TRUENAS_URL` es incorrecta, verás errores similares a los del test con token.

**3. Test de Subida a S3 (ejemplo con Autenticación por Token)**:

*   **Prerrequisitos Adicionales**:
    - Un bucket S3 debe existir y ser accesible con las credenciales proporcionadas.
    - `boto3` debe estar instalado (incluido en `requirements.txt`).
*   **Configuración del archivo `.env`**:
    Asegúrate de que tu archivo `.env` incluya las variables de TrueNAS y S3:
    ```dotenv
    TRUENAS_URL=http://<tu-truenas>/api/v2.0/system/config/save
    AUTH_METHOD=token
    API_KEY=tu_api_key_valida

    S3_ENDPOINT_URL=http://<tu-s3-endpoint> 
    S3_ACCESS_KEY_ID=tu_access_key_s3
    S3_SECRET_ACCESS_KEY=tu_secret_key_s3
    S3_BUCKET_NAME=tu_bucket_s3
    S3_REGION=tu_region_s3 # Opcional
    DELETE_LOCAL_BACKUP_AFTER_UPLOAD=true # O 'false' para conservar el archivo local
    ```
*   **Ejecución del Script**:
    ```bash
    python true-backup.py
    ```
*   **Verificación de Éxito**:
    - Mensajes de descarga de backup exitosa (como en los tests anteriores).
    - Mensaje: `Intentando subir <nombre_archivo> a S3 bucket <S3_BUCKET_NAME> en <S3_ENDPOINT_URL>...`
    - Mensaje: `Backup <nombre_archivo> subido correctamente al bucket <S3_BUCKET_NAME>.`
    - Verifica que el archivo de backup (`.db`) aparezca en tu bucket S3.
    - Si `DELETE_LOCAL_BACKUP_AFTER_UPLOAD` es `true`, deberías ver: `Archivo de backup local <nombre_archivo> eliminado correctamente.` y el archivo local ya no existirá.
    - Si `DELETE_LOCAL_BACKUP_AFTER_UPLOAD` es `false` (o no está definido), deberías ver: `Archivo de backup local <nombre_archivo> conservado.` y el archivo local persistirá.
*   **Verificación de Fallo (S3)**:
    - Si las variables S3 no están completas: `Configuración S3 no proporcionada o incompleta. Saltando subida a S3.`
    - Credenciales S3 incorrectas: `Error: Credenciales S3 no disponibles o incorrectas.`, `Error S3: AWS Access Key ID inválido.`, `Error S3: AWS Secret Access Key es incorrecto.`, o `Error S3: Acceso denegado...`
    - Bucket no encontrado: `Error S3: El bucket '<S3_BUCKET_NAME>' no existe.`
    - Problemas de red o endpoint S3 incorrecto: Pueden variar, incluyendo errores de conexión.
    - En caso de fallo en la subida a S3, el script indicará: `Archivo de backup local <nombre_archivo> conservado debido a un error en la subida a S3.`

**Nota Adicional**:
Aunque el script muestra mensajes de éxito o error, si tienes dudas sobre si la operación de backup se realizó correctamente en el servidor TrueNAS (especialmente en caso de respuestas ambiguas o si quieres confirmar que el backup generado es válido), puedes revisar los logs del sistema en la interfaz de usuario de TrueNAS. Para S3, siempre verifica el contenido del bucket.

## Uso

Ejecuta cualquiera de los scripts:
```bash
python check-pools-token.py
python true-backup.py
```
Asegúrate de que el archivo `.env` esté configurado correctamente en el mismo directorio desde donde ejecutas el script.

## Variables de Entorno Generales

- `TRUENAS_URL`: URL base de la API de TrueNAS (para scripts como `check-pools-*`) o URL del endpoint específico (para `true-backup.py`). Es importante verificar la URL requerida por cada script.
- `API_KEY`: Token de autenticación para la API. Usado por `check-pools-token.py` y por `true-backup.py` cuando `AUTH_METHOD` es `token`.
- `TRUENAS_USER`: Nombre de usuario para autenticación básica. Usado por `check-pools-basic-auth.py` y por `true-backup.py` cuando `AUTH_METHOD` es `basic`.
- `TRUENAS_PASS`: Contraseña para autenticación básica. Usado por `check-pools-basic-auth.py` y por `true-backup.py` cuando `AUTH_METHOD` es `basic`.
- `AUTH_METHOD`: Específico para `true-backup.py`. Define el método de autenticación (`token` o `basic`).

**Variables Específicas para S3 (usadas por `true-backup.py`)**:
- `S3_ENDPOINT_URL`: URL del endpoint S3.
- `S3_ACCESS_KEY_ID`: Access Key ID para S3.
- `S3_SECRET_ACCESS_KEY`: Secret Access Key para S3.
- `S3_BUCKET_NAME`: Nombre del bucket S3.
- `S3_REGION`: Región S3 (opcional).
- `DELETE_LOCAL_BACKUP_AFTER_UPLOAD`: Controla si el backup local se elimina tras una subida exitosa a S3 (`true`, `yes`, `1` para eliminar).

## Error Handling

Los scripts proporcionan mensajes de error si faltan variables de entorno requeridas para la operación seleccionada (por ejemplo, `API_KEY` para autenticación por token) o si ocurren problemas durante la conexión con TrueNAS (errores HTTP, problemas de red, etc.). Revisa la salida del script para más detalles en caso de problemas.
