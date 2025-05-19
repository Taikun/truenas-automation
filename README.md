# TrueNAS Client

Un conjunto de scripts en Python para interactuar con la API de TrueNAS.

## Scripts disponibles

- `check-pools-basic-auth.py`: Muestra el estado de los pools usando autenticación básica
- `check-pools-token.py`: Muestra el estado de los pools usando token de autenticación
- `true-backup.py`: Script para hacer backup de la configuración del sistema

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
API_KEY=tu-token-de-api
TRUENAS_USER=truenas-user
TRUENAS_PASS=truenas-user-pass
```

## Uso

Ejecuta cualquiera de los scripts:
```bash
python check-pools-token.py
python true-backup.py
```

## Variables de entorno

- `TRUENAS_URL`: URL base de la API de TrueNAS
- `API_KEY`: Token de autenticación para la API
