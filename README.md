# TrueNAS Client

Un conjunto de scripts en Python para interactuar con la API de TrueNAS.

## Scripts disponibles

- `check_truenas_status.py`: Script principal para monitorear el estado de TrueNAS. Ofrece una vista detallada del sistema, incluyendo información general, estado de los pools, datasets, espacio para aplicaciones, y alertas. Soporta autenticación básica y por token, y puede generar la salida en formato visual (Rich "Pip-Boy" style) o JSON. También incluye la opción de descargar un backup de la configuración del sistema.
- `true-backup.py`: Script dedicado para descargar un backup de la configuración del sistema TrueNAS. Soporta autenticación básica y por token, y opcionalmente sube el backup a un servicio S3 compatible.

**Scripts Anteriores (Obsoletos):**
Los scripts `check-pools-basic-auth.py` y `check-pools-token.py` han sido reemplazados por `check_truenas_status.py` y se consideran obsoletos. Se recomienda migrar al nuevo script para obtener todas las funcionalidades y mejoras.

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
Crea un archivo `.env` con las variables necesarias para los scripts que planeas usar.

**Ejemplo de archivo `.env`:**
```dotenv
# --- Configuración General de TrueNAS (usada por todos los scripts) ---
# URL de la API de TrueNAS (asegúrate que termine con /api/v2.0/)
TRUENAS_URL=https://tu-servidor-truenas/api/v2.0/

# --- Autenticación para TrueNAS (elige un método) ---
# Método de autenticación: 'token' o 'basic'.
# Usado por true-backup.py y check_truenas_status.py.
# Si se omite, 'token' es el valor por defecto para true-backup.py.
# Para check_truenas_status.py, si se omite, se intentará 'token' y luego podría fallar si API_KEY no está.
AUTH_METHOD=token 

# Si AUTH_METHOD=token:
API_KEY=tu-api-key-de-truenas

# Si AUTH_METHOD=basic:
TRUENAS_USER=tu-usuario-de-truenas
TRUENAS_PASS=tu-contraseña-de-truenas

# --- Configuración Específica para true-backup.py (Subida a S3 - Opcional) ---
# S3_ENDPOINT_URL=http://tu-s3-endpoint:9000
# S3_ACCESS_KEY_ID=tu-s3-access-key
# S3_SECRET_ACCESS_KEY=tu-s3-secret-key
# S3_BUCKET_NAME=nombre-de-tu-bucket
# S3_REGION=us-east-1 # Opcional
# DELETE_LOCAL_BACKUP_AFTER_UPLOAD=false # Opcional, 'true' para eliminar
```
**Nota Importante sobre `TRUENAS_URL`**:
- Para `check_truenas_status.py`, la URL debe ser la base de la API v2.0, por ejemplo, `https://<tu-truenas>/api/v2.0/`.
- Para `true-backup.py`, la URL debe ser el endpoint específico para descargar el archivo de configuración, por ejemplo, `http://<tu-truenas>/api/v2.0/system/config/save` (si usas API v2.0 para el backup) o el endpoint directo si no es API v2.0.

### Configuración Detallada para `check_truenas_status.py`

El script `check_truenas_status.py` es la herramienta principal para monitorear tu instancia de TrueNAS.

**Características Principales**:
- **Autenticación Unificada**: Soporta autenticación básica (`basic`) y por token (`token`) mediante la variable de entorno `AUTH_METHOD`.
- **Formatos de Salida Duales**:
    - `rich`: (Por defecto) Una interfaz visual estilo "Pip-Boy" para fácil lectura humana.
    - `json`: (Mediante `python check_truenas_status.py -o json`) Salida estructurada en JSON, ideal para integración con otras herramientas, scripts, o sistemas de automatización como N8N.
- **Recopilación Exhaustiva de Datos**:
    - **Información General del Sistema**: Hostname, versión de TrueNAS, tiempo de actividad (uptime), hora del sistema, detalles de la build, memoria física.
    - **Detalles de Pools**: Estado, uso de espacio (tamaño total, disponible, porcentaje usado), errores de lectura/escritura/checksum, fragmentación, estado de resilvering (incluyendo progreso), y detalles de los discos físicos asociados (temperatura, estado SMART).
    - **Detalles de Datasets por Pool**: Nombre, punto de montaje, espacio usado y disponible, cuotas, ratio de compresión, estado de solo lectura, tamaño de registro (record size), y estado de la deduplicación.
    - **Espacio para Aplicaciones**: Espacio disponible actualmente para aplicaciones (usualmente en el pool `ix-applications`).
    - **Alertas del Sistema**: Lista de alertas activas y resueltas, incluyendo severidad, descripción, y marca de tiempo.
- **Descarga de Backup**: Opción interactiva para descargar un backup de la configuración del sistema al finalizar la visualización en modo `rich`.

**Variables de Entorno (ver sección "Variables de Entorno" para detalles)**:
- `TRUENAS_URL`: URL base de la API v2.0 de TrueNAS (ej. `https://<tu-truenas>/api/v2.0/`).
- `AUTH_METHOD`: `token` o `basic`.
- `API_KEY`: Si `AUTH_METHOD=token`.
- `TRUENAS_USER`, `TRUENAS_PASS`: Si `AUTH_METHOD=basic`.

**Opciones de Línea de Comandos**:
- `-o json` o `--output-format json`: Cambia la salida a formato JSON.
- `-o rich` o `--output-format rich`: (Por defecto) Usa la salida visual Rich.

**Detalles de la Salida JSON**:
La salida JSON está diseñada para ser fácilmente parseable y utilizada en automatizaciones.
- `timestamp`: Marca de tiempo en formato ISO 8601 UTC de cuándo se generó el informe.
- `system_info`:
    - `truenas_url`, `auth_method`, `verify_ssl` (del script).
    - `hostname`, `version`, `buildtime`, `system_time_iso`, `uptime_seconds`, `license` (modelo), `physmem_gb` (del sistema TrueNAS).
- `pools`: Array de objetos, cada uno representando un pool.
    - `name`, `status`, `guid`, `size_bytes`, `allocated_bytes`, `available_bytes`, `used_percent`, `read_errors`, `write_errors`, `checksum_errors`, `fragmentation_percent`, `autotrim`.
    - `resilvering`: Objeto con `active` (boolean) y `progress_percent` (float).
    - `topology`: Objeto crudo de la topología del pool.
    - `disks`: Array de discos en el pool (`name`, `serial`, `type`, `size_bytes`, `temperature_celsius`, `smart_enabled`, `smart_passed`, `model`).
    - `datasets`: Array de datasets en el pool.
        - `name`, `pool_name`, `mountpoint`, `used_bytes`, `available_bytes`, `quota_bytes`, `compression_ratio` (string "2.50x"), `readonly` (boolean), `record_size_bytes`, `deduplication`, `sync`, `compression`, `atime`.
- `applications`: Objeto con `available_space_gb` (float o null) y `error` (string o null).
- `alerts_events`: Array de objetos de alerta.
    - `id`, `level` (ej. "CRITICAL"), `description`, `timestamp_iso`, `dismissed` (boolean), `source`.

**Ejemplo de Snippet JSON (estructura simplificada)**:
```json
{
  "timestamp": "2023-11-20T10:30:00.123456+00:00",
  "system_info": {
    "truenas_url": "https://truenas.local/api/v2.0/",
    "auth_method": "token",
    "verify_ssl": false,
    "hostname": "truenas-server",
    "version": "TrueNAS-SCALE-22.12.4.2",
    // ... más campos de system_info
  },
  "pools": [
    {
      "name": "mainpool",
      "status": "ONLINE",
      "size_bytes": 1099511627776,
      // ... más campos de pool
      "datasets": [
        {
          "name": "mainpool/mydata",
          "used_bytes": 53687091200,
          // ... más campos de dataset
        }
      ],
      "disks": [
        {
          "name": "sda",
          "temperature_celsius": 35,
          // ... más campos de disco
        }
      ]
    }
  ],
  "applications": {
    "available_space_gb": 123.45,
    "error": null
  },
  "alerts_events": [
    {
      "id": "somealertid",
      "level": "WARNING",
      "description": "Un disco reportó un error SMART.",
      // ... más campos de alerta
    }
  ]
}
```

**Detalles de la Salida Rich (Pip-Boy)**:
- **Panel de Información del Sistema**: Muestra hostname, versión de TrueNAS, tiempo de actividad, memoria física y fecha de build.
- **Paneles de Pools**: Cada pool tiene su propio panel mostrando:
    - Estado general y uso de espacio (con barra de progreso).
    - Errores de lectura/escritura/checksum.
    - Detalles técnicos como estado de resilvering y fragmentación.
    - Resumen de datasets (cantidad y espacio total usado).
    - Lista de discos físicos con su estado SMART y temperatura.
- **Panel de Aplicaciones**: Muestra el espacio disponible para aplicaciones.
- **Panel de Alertas del Sistema**: Lista las alertas activas, coloreadas por severidad (CRITICAL, WARNING, INFO), con su descripción, ID y fecha.

### Configuración Detallada para `check_truenas_status.py`

El script `check_truenas_status.py` es la herramienta principal para monitorear tu instancia de TrueNAS.

**Características Principales**:
- **Autenticación Unificada**: Soporta autenticación básica (`basic`) y por token (`token`) mediante la variable de entorno `AUTH_METHOD`.
- **Formatos de Salida Duales**:
    - `rich`: (Por defecto) Una interfaz visual estilo "Pip-Boy" para fácil lectura humana.
    - `json`: (Mediante `python check_truenas_status.py -o json`) Salida estructurada en JSON, ideal para integración con otras herramientas, scripts, o sistemas de automatización como N8N.
- **Recopilación Exhaustiva de Datos**:
    - **Información General del Sistema**: Hostname, versión de TrueNAS, tiempo de actividad (uptime), hora del sistema, detalles de la build, memoria física.
    - **Detalles de Pools**: Estado, uso de espacio (tamaño total, disponible, porcentaje usado), errores de lectura/escritura/checksum, fragmentación, estado de resilvering (incluyendo progreso), y detalles de los discos físicos asociados (temperatura, estado SMART).
    - **Detalles de Datasets por Pool**: Nombre, punto de montaje, espacio usado y disponible, cuotas, ratio de compresión, estado de solo lectura, tamaño de registro (record size), y estado de la deduplicación.
    - **Espacio para Aplicaciones**: Espacio disponible actualmente para aplicaciones (usualmente en el pool `ix-applications`).
    - **Alertas del Sistema**: Lista de alertas activas y resueltas, incluyendo severidad, descripción, y marca de tiempo.
- **Descarga de Backup**: Opción interactiva para descargar un backup de la configuración del sistema al finalizar la visualización en modo `rich`.

**Variables de Entorno (ver sección "Variables de Entorno" para detalles)**:
- `TRUENAS_URL`: URL base de la API v2.0 de TrueNAS (ej. `https://<tu-truenas>/api/v2.0/`).
- `AUTH_METHOD`: `token` o `basic`.
- `API_KEY`: Si `AUTH_METHOD=token`.
- `TRUENAS_USER`, `TRUENAS_PASS`: Si `AUTH_METHOD=basic`.

**Opciones de Línea de Comandos**:
- `-o json` o `--output-format json`: Cambia la salida a formato JSON.
- `-o rich` o `--output-format rich`: (Por defecto) Usa la salida visual Rich.

**Detalles de la Salida JSON**:
La salida JSON está diseñada para ser fácilmente parseable y utilizada en automatizaciones. Los valores de bytes son números enteros y las marcas de tiempo están en formato ISO 8601 UTC.
- `timestamp`: Marca de tiempo de cuándo se generó el informe.
- `system_info`:
    - `truenas_url`, `auth_method`, `verify_ssl` (configuración del script).
    - `hostname`, `version`, `buildtime`, `system_time_iso`, `uptime_seconds`, `license` (modelo del sistema, si aplica), `physmem_gb` (memoria física total en GB).
- `pools`: Array de objetos, cada uno representando un pool.
    - `name`, `status`, `guid`, `size_bytes`, `allocated_bytes`, `available_bytes`, `used_percent`, `read_errors`, `write_errors`, `checksum_errors`, `fragmentation_percent`, `autotrim` (estado).
    - `resilvering`: Objeto con `active` (boolean) y `progress_percent` (float).
    - `topology`: Objeto crudo de la topología del pool (puede ser extenso).
    - `disks`: Array de discos físicos en el pool (`name`, `serial`, `type`, `size_bytes`, `temperature_celsius`, `smart_enabled`, `smart_passed` (boolean), `model`, `description`).
    - `datasets`: Array de datasets dentro de este pool.
        - `name` (ID completo del dataset), `pool_name`, `mountpoint`, `used_bytes`, `available_bytes`, `quota_bytes` (si está definida), `compression_ratio` (string "X.XXx"), `readonly` (boolean), `record_size_bytes`, `deduplication`, `sync`, `compression`, `atime`.
- `applications`: Objeto con `available_space_gb` (float o `null`) y `error` (string o `null`).
- `alerts_events`: Array de objetos de alerta.
    - `id`, `level` (ej. "CRITICAL", "WARNING", "INFO"), `description` (texto completo del mensaje), `timestamp_iso`, `dismissed` (boolean), `source`.

**Ejemplo de Snippet JSON (estructura simplificada)**:
```json
{
  "timestamp": "2023-11-20T10:30:00.123456+00:00",
  "system_info": {
    "truenas_url": "https://truenas.local/api/v2.0/",
    "auth_method": "token",
    "verify_ssl": false,
    "hostname": "truenas-server",
    "version": "TrueNAS-SCALE-22.12.4.2",
    "uptime_seconds": 1234567,
    "physmem_gb": 31.25
  },
  "pools": [
    {
      "name": "mainpool",
      "status": "ONLINE",
      "size_bytes": 1099511627776,
      "available_bytes": 549755813888,
      "used_percent": 50.0,
      "datasets": [
        {
          "name": "mainpool/mydata",
          "used_bytes": 53687091200,
          "available_bytes": 214748364800,
          "compression_ratio": "1.50x"
        }
      ],
      "disks": [
        {
          "name": "sda",
          "model": "INTEL SSDSC2BB...",
          "temperature_celsius": 35,
          "smart_passed": true
        }
      ]
    }
  ],
  "applications": {
    "available_space_gb": 123.45,
    "error": null
  },
  "alerts_events": [
    {
      "id": "somealertid",
      "level": "WARNING",
      "description": "Un disco reportó un error SMART.",
      "timestamp_iso": "2023-11-19T08:15:00.000000+00:00",
      "dismissed": false
    }
  ]
}
```

**Detalles de la Salida Rich (Pip-Boy)**:
- **Panel de Información del Sistema**: Muestra hostname, versión de TrueNAS, tiempo de actividad, memoria física y fecha de build.
- **Paneles de Pools**: Cada pool tiene su propio panel mostrando:
    - Estado general y uso de espacio (con barra de progreso).
    - Errores de lectura/escritura/checksum.
    - Detalles técnicos como estado de resilvering y fragmentación.
    - Resumen de datasets (cantidad y espacio total usado).
    - Lista de discos físicos con su estado SMART y temperatura.
- **Panel de Aplicaciones**: Muestra el espacio disponible para aplicaciones.
- **Panel de Alertas del Sistema**: Lista las alertas activas, coloreadas por severidad (CRITICAL, WARNING, INFO), con su descripción (primera línea), ID y fecha/hora.

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

### Pruebas Manuales

Esta sección describe cómo probar manualmente los scripts actualizados.

**1. Pruebas para `check_truenas_status.py`**:

*   **Prerrequisitos**:
    - Instancia de TrueNAS accesible y configurada en `.env`.
    - `jq` (opcional, para visualizar JSON): `sudo apt-get install jq`
*   **Test de Salida Rich (Pip-Boy)**:
    ```bash
    python check_truenas_status.py
    ```
    Verifica que la información mostrada (info del sistema, pools, datasets, apps, alertas) sea correcta y la interfaz sea legible. Prueba la opción de descargar el backup.
*   **Test de Salida JSON**:
    ```bash
    python check_truenas_status.py -o json
    ```
    O para una vista formateada:
    ```bash
    python check_truenas_status.py -o json | jq .
    ```
    Verifica la estructura del JSON y que todos los campos esperados estén presentes y con valores correctos (hostname, versión, uptime, pools, datasets, alertas, etc.).
*   **Test con Diferentes Métodos de Autenticación**:
    Modifica `AUTH_METHOD` en tu archivo `.env` a `basic` (asegurándote que `TRUENAS_USER` y `TRUENAS_PASS` estén configurados) y repite los tests anteriores.

**2. Pruebas para `true-backup.py`**:

*   **Prerrequisitos**:
    - Instancia de TrueNAS accesible y configurada en `.env`.
    - Para la subida a S3: un bucket S3 accesible y las variables S3 configuradas en `.env`.
*   **Test de Backup Local (Autenticación por Token)**:

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

Ejecuta los scripts de la siguiente manera:
```bash
python check_truenas_status.py [opciones]
python true-backup.py
```
Asegúrate de que el archivo `.env` esté configurado correctamente en el mismo directorio desde donde ejecutas el script. `check_truenas_status.py` tiene opciones de línea de comandos (ver su sección específica).

## Variables de Entorno

Esta sección describe las variables de entorno utilizadas por los scripts.

**Para `check_truenas_status.py` y `true-backup.py`**:
- `TRUENAS_URL`: URL de la API de TrueNAS.
  - Para `check_truenas_status.py`: Debe ser la URL base de la API v2.0 (ej. `https://<tu-truenas>/api/v2.0/`). El script internamente añade `/` si es necesario y construye las rutas a los endpoints específicos (`/pool`, `/system/info`, etc.).
  - Para `true-backup.py`: Debe ser la URL del endpoint específico para descargar el archivo de configuración (ej. `http://<tu-truenas>/api/v2.0/system/config/save` o el endpoint directo si no es API v2.0).
- `AUTH_METHOD`: Define el método de autenticación. Puede ser:
    - `token` (valor por defecto en `true-backup.py` y `check_truenas_status.py`): Usa `API_KEY`.
    - `basic`: Usa `TRUENAS_USER` y `TRUENAS_PASS`.
- `API_KEY`: Tu API Key de TrueNAS. Necesaria si `AUTH_METHOD` es `token`.
- `TRUENAS_USER`: Tu nombre de usuario de TrueNAS. Necesario si `AUTH_METHOD` es `basic`.
- `TRUENAS_PASS`: Tu contraseña de TrueNAS. Necesaria si `AUTH_METHOD` es `basic`.

**Específicas para `true-backup.py` (Subida a S3)**:
- `S3_ENDPOINT_URL`: URL del endpoint de tu servicio S3.
- `S3_ACCESS_KEY_ID`: Tu Access Key ID de S3.
- `S3_SECRET_ACCESS_KEY`: Tu Secret Access Key de S3.
- `S3_BUCKET_NAME`: El nombre del bucket S3.
- `S3_REGION`: La región S3 (opcional).
- `DELETE_LOCAL_BACKUP_AFTER_UPLOAD`: Si se establece a `true`, `yes`, o `1`, el archivo de backup local se eliminará después de una subida exitosa a S3. Por defecto, se conserva (`false`).

**Nota sobre `VERIFY_SSL` en `check_truenas_status.py`**:
Actualmente, la verificación de certificados SSL está deshabilitada (`VERIFY_SSL = False`) directamente en el script `check_truenas_status.py` por simplicidad y para evitar problemas comunes en entornos domésticos con certificados autofirmados. Si necesitas habilitar la verificación SSL, deberás modificar esta variable directamente en el script.

## Error Handling

Los scripts proporcionan mensajes de error si faltan variables de entorno requeridas para la operación seleccionada (por ejemplo, `API_KEY` para autenticación por token) o si ocurren problemas durante la conexión con TrueNAS (errores HTTP, problemas de red, etc.). Revisa la salida del script para más detalles en caso de problemas.
