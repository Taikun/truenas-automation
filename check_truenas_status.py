import requests
import urllib3
from requests.auth import HTTPBasicAuth
from datetime import datetime, timezone # Added timezone
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.style import Style
from dotenv import load_dotenv
import os
import sys
import json # Added json
import argparse # Added argparse

# --- Global Configuration ---
console = Console() # Used only for Rich output
VERIFY_SSL = False # Both original scripts disable SSL verification
_output_format = "rich" # Global to control conditional printing

# Disable SSL warnings if verification is off
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Environment Variable Loading and Validation ---
load_dotenv()

TRUENAS_URL = os.getenv('TRUENAS_URL')
API_KEY = os.getenv('API_KEY')
TRUENAS_USER = os.getenv('TRUENAS_USER')
TRUENAS_PASS = os.getenv('TRUENAS_PASS')
AUTH_METHOD = os.getenv('AUTH_METHOD', 'token').lower()

# Conditional console print function
def cprint(message, style=None):
    if _output_format == "rich":
        console.print(message, style=style if style else Style())


if not TRUENAS_URL:
    cprint("[bold red]Error: TRUENAS_URL no está configurada en el archivo .env.[/bold red]")
    sys.exit(1)

if not TRUENAS_URL.endswith('/'):
    TRUENAS_URL += '/'

# --- Requests Session Setup ---
# This setup needs to happen after _output_format is set by argparse if we want cprint to work
session = requests.Session()

def setup_session():
    global session # Allow modification of the global session object
    session.verify = VERIFY_SSL

    if AUTH_METHOD == 'basic':
        if not TRUENAS_USER or not TRUENAS_PASS:
            cprint("[bold red]Error: TRUENAS_USER y TRUENAS_PASS son necesarios para la autenticación básica.[/bold red]")
            sys.exit(1)
        session.auth = HTTPBasicAuth(TRUENAS_USER, TRUENAS_PASS)
        cprint("[dim]Usando autenticación básica.[/dim]")
    elif AUTH_METHOD == 'token':
        if not API_KEY:
            cprint("[bold red]Error: API_KEY es necesario para la autenticación por token.[/bold red]")
            sys.exit(1)
        session.headers.update({"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
        cprint("[dim]Usando autenticación por token.[/dim]")
    else:
        cprint(f"[bold red]Error: Método de autenticación '{AUTH_METHOD}' no soportado. Use 'basic' o 'token'.[/bold red]")
        sys.exit(1)

# --- API Interaction ---
def make_api_request(endpoint_path, method="GET", params=None, json_data=None, stream=False):
    """
    Realiza una solicitud a la API de TrueNAS usando la sesión configurada.
    """
    full_url = TRUENAS_URL.rstrip('/') + '/' + endpoint_path.lstrip('/')
    try:
        response = session.request(method, full_url, params=params, json=json_data, stream=stream, timeout=10)
        response.raise_for_status()
        if stream:
            return response
        return response.json()
    except requests.exceptions.HTTPError as e:
        cprint(f"[bold red]Error HTTP {e.response.status_code} para {full_url}: {e.response.text}[/bold red]")
    except requests.exceptions.ConnectionError as e:
        cprint(f"[bold red]Error de conexión para {full_url}: {e}[/bold red]")
    except requests.exceptions.Timeout:
        cprint(f"[bold red]Timeout para la solicitud a {full_url}[/bold red]")
    except requests.exceptions.RequestException as e:
        cprint(f"[bold red]Error en la solicitud a {full_url}: {e}[/bold red]")
    return None

# --- Utility Functions ---
def formatear_tamano(bytes_val):
    """Convierte bytes a una unidad legible"""
    if bytes_val is None:
        return "N/A"
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unidad}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

# --- Utility Functions --- Additional
def formatear_uptime(seconds):
    """Convierte segundos a un formato legible de días, horas, minutos."""
    if seconds is None:
        return "N/A"
    days = seconds // (24 * 3600)
    seconds %= (24 * 3600)
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"

def parse_truenas_datetime(dt_str):
    """Parsea fechas de TrueNAS API (ej: '2023-10-15T18:27:00.123Z' o '%Y-%m-%dT%H:%M:%S.%f') a ISO8601 UTC"""
    if not dt_str:
        return None
    try:
        # Handle timezone-aware strings ending with Z (UTC)
        if dt_str.endswith('Z'):
            dt_obj = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            # Attempt parsing common TrueNAS formats, assuming naive is UTC if no tzinfo
            # Common format: 2024-01-20T11:30:45
            # Common format with ms: 2024-01-20T11:30:45.123456
            try:
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
            dt_obj = dt_obj.replace(tzinfo=timezone.utc) # Assume UTC if naive

        return dt_obj.isoformat()
    except ValueError as e:
        cprint(f"[yellow]No se pudo parsear la fecha '{dt_str}': {e}[/yellow]")
        return None


# --- Data Fetching Functions ---
def obtener_system_general_info():
    """Obtiene información general del sistema TrueNAS."""
    cprint("[dim]Obteniendo información general del sistema...[/dim]")
    data = make_api_request("system/info")
    if not data:
        return {"error": "No se pudo obtener la información del sistema."}
    
    uptime_seconds = None
    if data.get("uptime_seconds"): # TrueNAS Scale
        uptime_seconds = data["uptime_seconds"]
    elif data.get("uptime"): # TrueNAS Core might have "Uptime: 1 day, 2 hours..."
        # Parsing uptime string is complex, prefer uptime_seconds if available
        # For now, if only string uptime, we'll mark as N/A for seconds
        pass # Keep uptime_seconds as None if not directly available as seconds

    return {
        "hostname": data.get("hostname"),
        "version": data.get("version"),
        "buildtime": data.get("buildtime", {}).get("$date") if isinstance(data.get("buildtime"), dict) else data.get("buildtime"),
        "system_time_iso": parse_truenas_datetime(data.get("datetime")),
        "uptime_seconds": uptime_seconds,
        "license": data.get("license", {}).get("model") if isinstance(data.get("license"), dict) else None, # Example for Scale
        "physmem_gb": round(data.get("physmem", 0) / (1024**3), 2) if data.get("physmem") else None # Physmem is in bytes
    }

def obtener_all_datasets_info():
    """Obtiene información detallada de todos los datasets."""
    cprint("[dim]Obteniendo información de todos los datasets...[/dim]")
    datasets_raw = make_api_request("pool/dataset")
    if not datasets_raw:
        return []
    
    datasets_info = []
    for ds in datasets_raw:
        used_info = ds.get("used", {})
        quota_info = ds.get("quota", {}) # quota can be like {"quota": value} or {"refquota": value}
        
        quota_bytes = None
        if quota_info.get("quota") is not None and quota_info["quota"] > 0 : # 0 often means no quota
            quota_bytes = quota_info["quota"]
        elif quota_info.get("refquota") is not None and quota_info["refquota"] > 0:
             quota_bytes = quota_info["refquota"]

        datasets_info.append({
            "name": ds.get("id"), # 'id' is usually the full dataset name like 'pool/parent/child'
            "pool_name": ds.get("pool"),
            "mountpoint": ds.get("mountpoint"),
            "used_bytes": used_info.get("bytes"),
            "available_bytes": ds.get("available", {}).get("bytes"),
            "quota_bytes": quota_bytes,
            "compression_ratio": ds.get("compressratio", {}).get("value"), # format "1.23x" needs parsing
            "readonly": ds.get("readonly", {}).get("value") == "on", # "on" or "off"
            "record_size_bytes": ds.get("refrecordsize", {}).get("value") or ds.get("recordsize", {}).get("value"), # refrecordsize or recordsize
            "deduplication": ds.get("dedup", {}).get("value"), # "on", "off", "verify", etc.
            "sync": ds.get("sync", {}).get("value"),
            "compression": ds.get("compression", {}).get("value"),
            "atime": ds.get("atime", {}).get("value")
        })
    return datasets_info

def obtener_alerts_info():
    """Obtiene la lista de alertas del sistema."""
    cprint("[dim]Obteniendo alertas del sistema...[/dim]")
    alerts_raw = make_api_request("alert/list")
    if not alerts_raw:
        return []
    
    alerts_info = []
    for alert in alerts_raw:
        # Datetime parsing: TrueNAS alert datetime can be complex.
        # Example: alert['datetime']['$date'] might be a Unix timestamp in milliseconds.
        # Or it might be a string.
        alert_ts_iso = None
        if isinstance(alert.get("datetime"), dict) and "$date" in alert["datetime"]:
            try:
                # Assuming $date is Unix timestamp in milliseconds
                ts_seconds = alert["datetime"]["$date"] / 1000
                alert_ts_iso = datetime.fromtimestamp(ts_seconds, timezone.utc).isoformat()
            except Exception as e:
                cprint(f"[yellow]Error parseando timestamp de alerta: {alert['datetime']['$date']} - {e}[/yellow]")
        elif isinstance(alert.get("datetime"), str): # If it's already a string
             alert_ts_iso = parse_truenas_datetime(alert.get("datetime"))


        alerts_info.append({
            "id": alert.get("id"),
            "level": alert.get("klass"), # 'klass' is often used for level (e.g., CRITICAL, WARNING)
            "description": alert.get("formatted") or alert.get("title") or alert.get("message", "N/A"),
            "timestamp_iso": alert_ts_iso,
            "dismissed": alert.get("dismissed"),
            "source": alert.get("source") # if available
        })
    return alerts_info

def obtener_pools_info(all_datasets): # Modified to take all_datasets
    """Obtiene y procesa la información de los pools, discos y sus datasets. Devuelve datos crudos para JSON."""
    cprint("[dim]Obteniendo información de los pools...[/dim]")
    pools_raw = make_api_request("pool")
    cprint("[dim]Obteniendo información de los discos...[/dim]")
    disks_raw = make_api_request("disk")
    
    pools_data = []
    if not pools_raw:
        cprint("[yellow]No se pudo obtener la información de los pools.[/yellow]")
        return pools_data
    if not disks_raw:
        cprint("[yellow]No se pudo obtener la información de los discos. Se mostrarán los pools sin detalles de discos.[/yellow]")
        disks_raw = []

    for pool_api_data in pools_raw:
        scan_info = pool_api_data.get("scan", {})
        resilvering_active = scan_info.get("state") == "SCANNING" and scan_info.get("function") == "RESILVER"
        
        pool_info = {
            "name": pool_api_data.get("name"),
            "status": pool_api_data.get("status"),
            "guid": pool_api_data.get("guid"),
            "size_bytes": None, 
            "allocated_bytes": None, 
            "available_bytes": None, 
            "used_percent": None, 
            "read_errors": pool_api_data.get("read_errors", 0), 
            "write_errors": pool_api_data.get("write_errors", 0),
            "checksum_errors": pool_api_data.get("checksum_errors", 0),
            "fragmentation_percent": pool_api_data.get("fragmentation"), 
            "self_healed_bytes": pool_api_data.get("self_healed"), 
            "resilvering": {
                "active": resilvering_active,
                "progress_percent": scan_info.get("percentage", 0.0) if resilvering_active else 0.0
            },
            "autotrim": pool_api_data.get("autotrim"),
            "topology": pool_api_data.get("topology"), 
            "disks": [],
            "datasets": [] # New field for datasets
        }
        
        # Consolidate statistics gathering (size, allocated, etc.)
        # Try topology data first (common in Scale)
        if pool_api_data.get('topology') and pool_api_data['topology'].get('data'):
            total_size = 0
            total_allocated = 0
            has_topo_stats = False
            for vdev in pool_api_data['topology']['data']:
                if vdev.get('stats'):
                    has_topo_stats = True
                    stats = vdev['stats']
                    total_size += stats.get('size', 0)
                    total_allocated += stats.get('allocated', 0)
                    # Errors are usually per pool, but if vdev stats have them, could prioritize
                    if stats.get("read_errors") is not None: pool_info["read_errors"] = stats.get("read_errors")
                    if stats.get("write_errors") is not None: pool_info["write_errors"] = stats.get("write_errors")
                    if stats.get("checksum_errors") is not None: pool_info["checksum_errors"] = stats.get("checksum_errors")
            
            if has_topo_stats:
                pool_info["size_bytes"] = total_size
                pool_info["allocated_bytes"] = total_allocated
                if total_size > 0:
                    pool_info["available_bytes"] = total_size - total_allocated
                    pool_info["used_percent"] = round((total_allocated / total_size) * 100, 2) if total_size else 0.0
                else:
                    pool_info["available_bytes"] = 0
                    pool_info["used_percent"] = 0.0

        # Fallback to pool-level stats (common in Core or if no detailed vdev stats)
        if pool_info["size_bytes"] is None and pool_api_data.get("size") is not None:
            pool_info["size_bytes"] = pool_api_data.get("size")
            # TrueNAS API often provides 'free' rather than 'allocated' at pool level
            free_bytes = pool_api_data.get("free") 
            if free_bytes is not None:
                pool_info["available_bytes"] = free_bytes
                pool_info["allocated_bytes"] = pool_info["size_bytes"] - free_bytes
                if pool_info["size_bytes"] > 0:
                    pool_info["used_percent"] = round((pool_info["allocated_bytes"] / pool_info["size_bytes"]) * 100, 2)
                else:
                    pool_info["used_percent"] = 0.0
        
        # Ensure error counts are numbers, default to 0 if not found or None
        for err_type in ["read_errors", "write_errors", "checksum_errors"]:
            if pool_info[err_type] is None:
                pool_info[err_type] = 0


        # Assign disks
        for disk_item in disks_raw:
            if disk_item.get("pool") == pool_api_data.get("name"):
                pool_info["disks"].append({
                    "name": disk_item.get("name"),
                    "serial": disk_item.get("serial"),
                    "type": disk_item.get("type"),
                    "size_bytes": disk_item.get("size"),
                    "temperature_celsius": disk_item.get("temperature"),
                    "smart_enabled": disk_item.get("smart"),
                    "smart_passed": disk_item.get("smart_status") == "PASSED", 
                    "description": disk_item.get("description"),
                    "model": disk_item.get("model")
                })
        
        # Assign datasets to this pool
        pool_name = pool_api_data.get("name")
        if pool_name:
            for ds_info in all_datasets:
                # Check if dataset name starts with pool_name + "/" or is exactly pool_name
                if ds_info.get("name", "").startswith(pool_name + "/") or ds_info.get("name") == pool_name:
                    pool_info["datasets"].append(ds_info)
        
        pools_data.append(pool_info)
    return pools_data

def obtener_espacio_disponible_aplicaciones():
    """Obtiene el espacio disponible para aplicaciones. Devuelve un dict para JSON."""
    cprint("[dim]Obteniendo espacio disponible para aplicaciones...[/dim]")
    
    # Try /kubernetes/config first as per previous refinement
    data_k8s = make_api_request("kubernetes/config")
    if data_k8s and isinstance(data_k8s, dict):
        # Hypothetical key structures for k8s available space
        if "available_space_for_apps_bytes" in data_k8s and data_k8s["available_space_for_apps_bytes"] is not None:
            espacio_bytes = data_k8s["available_space_for_apps_bytes"]
            return {"available_space_gb": round(espacio_bytes / (1024 ** 3), 2), "error": None}
        elif "pool" in data_k8s and data_k8s["pool"]: # If it tells us the pool name
             cprint(f"[yellow]Endpoint /kubernetes/config no proveyó espacio directamente, pero indicó pool '{data_k8s['pool']}'. Esta ruta no está completamente implementada para extraer espacio de un pool específico aquí.[/yellow]")
             # Future: could fetch this specific pool's available space if needed.
    
    # Fallback to /app/available_space
    cprint("[dim]Intentando con endpoint alternativo /app/available_space...[/dim]")
    data_alt = make_api_request("app/available_space")
    if data_alt is not None:
        try:
            espacio_bytes = int(data_alt)
            return {"available_space_gb": round(espacio_bytes / (1024 ** 3), 2), "error": None}
        except (ValueError, TypeError):
            cprint(f"[yellow]Respuesta de /app/available_space no fue un número: {data_alt}[/yellow]")
            return {"available_space_gb": None, "error": f"Respuesta no válida de /app/available_space: {data_alt}"}

    cprint("[yellow]No se pudo obtener el espacio disponible para aplicaciones.[/yellow]")
    return {"available_space_gb": None, "error": "No se pudo obtener el espacio disponible para aplicaciones."}


def descargar_backup_config():
    """Descarga un backup de la configuración del sistema."""
    cprint("[dim]Iniciando descarga de backup de configuración...[/dim]")
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"truebackup_{now}.db"
    
    response = make_api_request(
        "config/save",
        method="POST",
        json_data={"secretseed": True, "root_authorized_keys": True},
        stream=True 
    )
    
    if response and response.ok:
        try:
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            cprint(f"[bold green]✅ Backup guardado como {filename}[/bold green]")
        except Exception as e:
            cprint(f"[bold red]❌ Error al guardar el archivo de backup {filename}: {e}[/bold red]")
    elif response:
        cprint(f"[bold red]❌ Falló la solicitud de backup (código {response.status_code}).[/bold red]")
    else:
        cprint("[bold red]❌ Falló la solicitud de backup (sin respuesta del servidor).[/bold red]")


# --- Display Logic ---
def mostrar_estado_pipboy(system_general_data, pools_info, app_space_info, alerts_data):
    """Muestra el estado de los pools y otra información en una interfaz visual."""
    
    console.clear()
    logo = r"""
    [green]
ooooooooo.    o8o                    .oooooo.     o8o           oooo  
`888   `Y88.  `"'                   d8P'  `Y8b    `"'           `888  
 888   .d88' oooo  oo.ooooo.       888           oooo  oooo d8b  888  
 888ooo88P'  `888   888' `88b      888           `888  `888""8P  888  
 888          888   888   888      888     ooooo  888   888      888  
 888          888   888   888      `88.    .88'   888   888      888  
o888o        o888o  888bod8P'       `Y8bood8P'   o888o d888b    o888o 
                    888                                               
                   o888o                                              
    [/green]
    """
    console.print(logo, justify="center")
    
    current_time_str = datetime.now().strftime("%H:%M:%S") # Local time for display
    console.print(f"[bold green]{current_time_str}[/bold green]", justify="center")
    console.rule("[bold green]ESTADO DEL SISTEMA TRUENAS[/bold green]")

    # System Info Panel
    sys_info_panel_content = [
        f"[cyan]Hostname:[/cyan] {system_general_data.get('hostname', 'N/A')}",
        f"[cyan]Versión TrueNAS:[/cyan] {system_general_data.get('version', 'N/A')}",
        f"[cyan]Uptime:[/cyan] {formatear_uptime(system_general_data.get('uptime_seconds'))}",
        f"[cyan]Memoria Física:[/cyan] {system_general_data.get('physmem_gb', 'N/A')} GB"
    ]
    if system_general_data.get('buildtime'):
        sys_info_panel_content.append(f"[cyan]Build Time:[/cyan] {parse_truenas_datetime(system_general_data.get('buildtime'))}")

    console.print(Panel("\n".join(sys_info_panel_content), title="[bold sky_blue1]Información del Sistema[/bold sky_blue1]", style="sky_blue1", border_style="sky_blue1"))
    console.print("")


    if not pools_info:
        console.print(Panel("[yellow]No se encontró información de pools o no se pudo acceder.[/yellow]", title="[bold yellow]Pools[/bold yellow]"))
    
    for pool in pools_info:
        nombre = pool.get("name", "N/A")
        estado = pool.get("status", "N/A")
        
        panel_title = f"[bold green]Pool:[/bold green] {nombre} - [bold green]Estado:[/bold green] {estado}"
        content_items = [] 

        size_bytes = pool.get("size_bytes") 
        available_bytes = pool.get("available_bytes")
        used_percent = pool.get("used_percent")

        if size_bytes is not None and available_bytes is not None and used_percent is not None:
            content_items.append(f"[green]Tamaño Total:[/green] {formatear_tamano(size_bytes)}")
            content_items.append(f"[green]Espacio Libre:[/green] {formatear_tamano(available_bytes)}")
            
            progress = Progress(
                TextColumn("[progress.description]{task.description}", style="green"),
                BarColumn(bar_width=None, complete_style="green", finished_style="green"),
                TextColumn("[green]{task.percentage:>3.0f}% usado"),
                console=console,
                expand=True
            )
            progress.add_task("Uso", total=100, completed=used_percent)
            content_items.append(progress)
        else:
            content_items.append("[yellow]Estadísticas de espacio no disponibles.[/yellow]")

        read_errors = pool.get("read_errors", 0)
        write_errors = pool.get("write_errors", 0)
        checksum_errors = pool.get("checksum_errors", 0)
        
        error_style_val = Style(color="red") if read_errors > 0 or write_errors > 0 or checksum_errors > 0 else Style(color="green")
        
        content_items.append(Text(f"Errores Lectura: {read_errors if read_errors is not None else 'N/A'}", style=error_style_val))
        content_items.append(Text(f"Errores Escritura: {write_errors if write_errors is not None else 'N/A'}", style=error_style_val))
        content_items.append(Text(f"Errores Checksum: {checksum_errors if checksum_errors is not None else 'N/A'}", style=error_style_val))

        details_content_items = []
        resilvering_data = pool.get("resilvering", {})
        resilver_info_str = f"[red]Sí (Progreso: {resilvering_data.get('progress_percent', 0.0):.2f}%)[/red]" if resilvering_data.get("active") else "[green]No[/green]"
        details_content_items.append(f"[green]Resilvering?:[/green] {resilver_info_str}")
        fragmentation = pool.get('fragmentation_percent')
        details_content_items.append(f"[green]Fragmentación:[/green] {fragmentation if fragmentation is not None else 'N/A'}%")
        
        if details_content_items:
             content_items.append(Panel("\n".join(details_content_items), title="[bold green]Detalles Técnicos[/bold green]", style="green", border_style="dim green"))
        
        # Dataset Info for Rich Output (Summary)
        datasets_in_pool = pool.get("datasets", [])
        if datasets_in_pool:
            total_datasets_space_used_bytes = sum(ds.get("used_bytes", 0) or 0 for ds in datasets_in_pool)
            dataset_summary = f"Total Datasets: {len(datasets_in_pool)}\nEspacio Usado por Datasets: {formatear_tamano(total_datasets_space_used_bytes)}"
            content_items.append(Panel(dataset_summary, title="[bold green]Resumen de Datasets[/bold green]", style="green", border_style="dim green"))

        discos = pool.get("disks", [])
        if discos:
            disco_lines = []
            for disco in discos:
                estado_disco = "[green]OK[/green]" if disco.get("smart_passed") else "[red]Fallo[/red]"
                temp = disco.get("temperature_celsius", "N/A")
                nombre_disco = disco.get("name", "N/A")
                disco_lines.append(f"{nombre_disco}: {estado_disco} - Temp: {temp}°C")
            content_items.append(Panel("\n".join(disco_lines), title="[bold green]Discos Físicos[/bold green]", style="green", border_style="dim green"))
        
        console.print(Panel("\n".join(str(c) for c in content_items), title=panel_title, style="green", border_style="bold green"))
        console.print("")

    app_space_gb_val = app_space_info.get("available_space_gb")
    app_space_error = app_space_info.get("error")
    app_display_text = f"{app_space_gb_val} GB" if app_space_gb_val is not None else f"[red]{app_space_error or 'No disponible'}[/red]"
    console.print(Panel(f"[bold green]Espacio disponible para Apps:[/bold green] {app_display_text}", style="cyan", title="[bold cyan]Aplicaciones[/bold cyan]"))
    console.print("")

    # Alerts Panel
    active_alerts = [alert for alert in alerts_data if not alert.get("dismissed")]
    if active_alerts:
        alert_panel_content = []
        for alert in active_alerts:
            level = alert.get("level", "INFO")
            color = "red" if level == "CRITICAL" else "yellow" if level == "WARNING" else "blue"
            desc = alert.get("description", "N/A").split('\n')[0] # First line for brevity
            ts = parse_truenas_datetime(alert.get("timestamp_iso")) or "N/A"
            alert_panel_content.append(f"[{color}]{level}: {desc} (ID: {alert.get('id')}, Time: {ts})[/{color}]")
        console.print(Panel("\n".join(alert_panel_content), title="[bold orange_red1]Alertas Activas del Sistema[/bold orange_red1]", style="orange_red1", border_style="orange_red1"))
    else:
        console.print(Panel("[green]No hay alertas activas en el sistema.[/green]", title="[bold green]Alertas del Sistema[/bold green]", style="green", border_style="green"))


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica el estado de TrueNAS y opcionalmente descarga un backup.")
    parser.add_argument(
        '-o', '--output-format',
        type=str,
        choices=['rich', 'json'],
        default='rich',
        help='Formato de salida (rich o json). Por defecto: rich.'
    )
    args = parser.parse_args()
    _output_format = args.output_format 

    setup_session() 
    
    cprint("[dim]Iniciando script de estado de TrueNAS...[/dim]")
    
    system_general_data = obtener_system_general_info()
    all_datasets_data = obtener_all_datasets_info()
    pools_informacion = obtener_pools_info(all_datasets_data) # Pass datasets to pool info
    espacio_apps_info = obtener_espacio_disponible_aplicaciones() 
    alerts_data = obtener_alerts_info()
    
    if _output_format == "json":
        # Merge existing system_info with new general system data
        current_system_info = {
            "truenas_url": TRUENAS_URL,
            "auth_method": AUTH_METHOD,
            "verify_ssl": VERIFY_SSL
        }
        system_info_combined = {**current_system_info, **system_general_data}

        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(), 
            "system_info": system_info_combined,
            "pools": pools_informacion, # Already contains datasets
            "applications": espacio_apps_info,
            "alerts_events": alerts_data
        }
        print(json.dumps(output_data, indent=2, default=str)) # default=str for any non-serializable data
        sys.exit(0)
    
    # Default to Rich output
    mostrar_estado_pipboy(system_general_data, pools_informacion, espacio_apps_info, alerts_data)
    
    try:
        respuesta = console.input("\n[bold cyan]¿Deseas guardar un backup de la configuración ahora? (s/n):[/bold cyan] ").strip().lower()
        if respuesta == "s":
            descargar_backup_config()
        else:
            cprint("[dim]Backup de configuración omitido.[/dim]")
    except KeyboardInterrupt:
        cprint("\n[yellow]Operación cancelada por el usuario.[/yellow]")
    finally:
        cprint("[dim]Script finalizado.[/dim]")
