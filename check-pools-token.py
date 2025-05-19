import requests
import urllib3
from datetime import datetime
import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.text import Text
from rich.style import Style
from dotenv import load_dotenv
import os

# Configuración de la API
load_dotenv()
TRUENAS_URL = os.getenv('TRUENAS_URL')
API_KEY = os.getenv('API_KEY')

# Verificar que la URL termine con / para evitar problemas de concatenación
if not TRUENAS_URL.endswith('/'):
    TRUENAS_URL += '/'

# Configuración de headers
def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

# Deshabilitar advertencias de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuración de la interfaz
console = Console()

# Funciones de formato
def formatear_tamano(bytes):
    """Convierte bytes a una unidad legible"""
    for unidad in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unidad}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

# Funciones de API
def obtener_pools():
    """Obtiene la lista de pools disponibles"""
    try:
        response = requests.get(
            f"{TRUENAS_URL}/pool",
            headers=get_headers(),
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error al consultar los pools: {e}")
        return []

def obtener_discos_pool(pool_id):
    """Obtiene la lista de discos de un pool específico"""
    try:
        response = requests.get(
            f"{TRUENAS_URL}/disk",
            headers=get_headers(),
            verify=False
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []

def espacio_disponible_aplicaciones():
    """Obtiene el espacio disponible para aplicaciones"""
    try:
        response = requests.get(
            f"{TRUENAS_URL}app/available_space",
            headers=get_headers(),
            verify=False,
            timeout=5
        )
        response.raise_for_status()
        espacio_bytes = response.json()
        espacio_gb = espacio_bytes / (1024 ** 3)
        return round(espacio_gb, 2)
    except requests.exceptions.Timeout:
        console.print("[bold red]❌ Timeout al intentar conectar con el servidor TrueNAS[/bold red]")
        return "No disponible"
    except requests.exceptions.ConnectionError as e:
        console.print(f"[bold red]❌ No se puede conectar con el servidor TrueNAS: {e}[/bold red]")
        return "No disponible"
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al consultar el espacio disponible: {e}[/bold red]")
        return "No disponible"
    except Exception as e:
        console.print(f"[bold red]❌ Error inesperado: {e}[/bold red]")
        return "No disponible"

def descargar_backup_config():
    """Descarga un backup de la configuración del sistema"""
    try:
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"truebackup_{now}.db"
        
        # Hacer la solicitud para crear el backup
        response = requests.post(
            f"{TRUENAS_URL}config/save",
            headers=get_headers(),
            json={
                "secretseed": True,
                "root_authorized_keys": True
            },
            verify=False
        )
        response.raise_for_status()
        
        # Guardar el archivo directamente ya que el endpoint devuelve el archivo
        with open(filename, "wb") as f:
            f.write(response.content)
        
        console.print(f"[bold green]✅ Backup guardado como {filename}[/bold green]")
        
    except requests.exceptions.HTTPError as e:
        console.print(f"[bold red]❌ Error HTTP: {e.response.status_code} - {e.response.text}[/bold red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al realizar el backup: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error inesperado: {e}[/bold red]")
        
        # Esperar a que el job termine
        while True:
            # Eliminar el código relacionado con el job ya que no es necesario
            job_response.raise_for_status()
            job_status = job_response.json()
            
            if job_status.get('state') == 'SUCCESS':
                break
            elif job_status.get('state') == 'FAILED':
                raise Exception(f"Job failed: {job_status.get('error')}")
            
            time.sleep(1)
        
        # Descargar el archivo
        download_response = requests.get(
            download_url,
            auth=HTTPBasicAuth("truenas_admin", "dlilu7"),
            verify=False,
            stream=True
        )
        download_response.raise_for_status()
        
        with open(filename, "wb") as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        console.print(f"[bold green]✅ Backup guardado como {filename}[/bold green]")
        
    except requests.exceptions.HTTPError as e:
        console.print(f"[bold red]❌ Error HTTP: {e.response.status_code} - {e.response.text}[/bold red]")
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]❌ Error al realizar el backup: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Error inesperado: {e}[/bold red]")

# Función principal de visualización
def mostrar_estado_pipboy(pools_info):
    """Muestra el estado de los pools en una interfaz visual"""
    def reloj_parpadeante(stop_event):
        """Animación de reloj parpadeante"""
        while not stop_event.is_set():
            hora_actual = datetime.now().strftime("%H:%M:%S")
            # Parpadeo: mostrar o no mostrar los dos puntos
            if int(time.time() * 2) % 2 == 0:
                reloj = f"[green]{hora_actual}[/green]"
            else:
                reloj = f"[green]{hora_actual.replace(':', ' ')}[/green]"
            console.print(reloj, justify="center", end="\r")
            time.sleep(0.5)

    # Configuración inicial
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
    console.rule("[bold green]ESTADO DE LOS POOLS[/bold green]")

    # Iniciar animación del reloj
    stop_event = threading.Event()
    hilo_reloj = threading.Thread(target=reloj_parpadeante, args=(stop_event,), daemon=True)
    hilo_reloj.start()

    # Mostrar información de cada pool
    for pool in pools_info:
        nombre = pool["name"]
        estado = pool["status"]
        size = pool.get("size")
        available = pool.get("available")
        used_percent = pool.get("used_percent")

        # Encabezado del pool
        text_header = f"[green]Nombre:[/green] {nombre}   [green]Estado:[/green] {estado}"
        console.print(Panel(text_header, style=Style(color="green")))

        # Mostrar detalles si están disponibles
        if size and available is not None and used_percent is not None:
            # Espacio y uso
            console.print(f"[green]Tamaño:[/green] {formatear_tamano(size)}")
            console.print(f"[green]Libre: [/green]{formatear_tamano(available)}")
            
            # Barra de progreso
            progress = Progress(
                TextColumn("[progress.description]{task.description}", style="green"),
                BarColumn(bar_width=40, complete_style="green", finished_style="green"),
                TextColumn("[green]{task.percentage:>3.0f}% usado"),
                console=console
            )
            task = progress.add_task("Uso", total=100, completed=used_percent)
            console.print(progress.get_renderable())

            # Errores
            read_errors = pool.get("read_errors", "N/A")
            write_errors = pool.get("write_errors", "N/A")
            checksum_errors = pool.get("checksum_errors", "N/A")

            # Alerta si hay errores
            alerta = False
            if any([
                isinstance(read_errors, int) and read_errors > 0,
                isinstance(write_errors, int) and write_errors > 0,
                isinstance(checksum_errors, int) and checksum_errors > 0
            ]):
                alerta = True
                console.bell()

            # Mostrar errores con color apropiado
            color = 'red' if alerta else 'green'
            console.print(f"[{color}]Errores de lectura:[/{color}] {read_errors}")
            console.print(f"[{color}]Errores de escritura:[/{color}] {write_errors}")
            console.print(f"[{color}]Errores de checksum:[/{color}] {checksum_errors}")

            # Detalles técnicos
            resilvering = pool.get("resilvering", False)
            resilver_info = "[red]Sí[/red]" if resilvering else "[green]No[/green]"

            fragmentation = pool.get("fragmentation", "N/A")
            self_healed = pool.get("self_healed", "N/A")
            configured_ashift = pool.get("configured_ashift", "N/A")
            logical_ashift = pool.get("logical_ashift", "N/A")
            physical_ashift = pool.get("physical_ashift", "N/A")

            ops = pool.get("ops", [])
            read_ops = ops[1] if len(ops) > 1 else "N/A"
            write_ops = ops[2] if len(ops) > 2 else "N/A"

            bytes_list = pool.get("bytes", [])
            read_bytes = bytes_list[1] if len(bytes_list) > 1 else 0
            write_bytes = bytes_list[2] if len(bytes_list) > 2 else 0

            # Panel de detalles técnicos
            extra_info = f"""
[green]¿Resilvering?:[/green] {resilver_info}
[green]Fragmentación:[/green] {fragmentation}%
[green]Self-Healed:[/green] {self_healed}
[green]Ashift (conf):[/green] {configured_ashift}
[green]Ashift lógico:[/green] {logical_ashift}
[green]Ashift físico:[/green] {physical_ashift}
[green]Lecturas/s:[/green] {read_ops}
[green]Escrituras/s:[/green] {write_ops}
[green]Bytes leídos:[/green] {formatear_tamano(read_bytes)}
[green]Bytes escritos:[/green] {formatear_tamano(write_bytes)}
"""
            console.print(Panel(extra_info.strip(), title="[bold green]Detalles técnicos[/bold green]", style="green"))

            # Panel de discos
            discos = pool.get("disks", [])
            if discos:
                disco_lines = []
                for disco in discos:
                    estado = "[green]OK[/green]" if disco.get("smart_status") else "[red]Fallo[/red]"
                    temp = disco.get("temperature", "N/A")
                    nombre = disco.get("name")
                    disco_lines.append(f"{nombre}: {estado} - Temp: {temp}°C")
                panel_disks = "\n".join(disco_lines)
                console.print(Panel(panel_disks, title="[bold green]Discos físicos[/bold green]", style="green"))
        else:
            console.print("[yellow]Información no disponible[/yellow]")

        console.print("\n")

    # Detener la animación del reloj
    stop_event.set()
    hilo_reloj.join(timeout=1)

if __name__ == "__main__":
    pools = obtener_pools()
    pools_data = []

    for pool in pools:
        topology_data = pool['topology']['data']
        if topology_data and isinstance(topology_data[0], dict) and 'stats' in topology_data[0]:
            stats = topology_data[0]['stats']
            size = stats.get('size')
            allocated = stats.get('allocated')

            if size and allocated is not None:
                available = size - allocated
                used_percent = round((allocated / size) * 100, 2)

                read_errors = stats.get("read_errors")
                write_errors = stats.get("write_errors")
                checksum_errors = stats.get("checksum_errors")

                fragmentation = stats.get("fragmentation")
                self_healed = stats.get("self_healed")
                configured_ashift = stats.get("configured_ashift")
                logical_ashift = stats.get("logical_ashift")
                physical_ashift = stats.get("physical_ashift")
                ops = stats.get("ops")
                bytes_io = stats.get("bytes")

                todos_los_disks = obtener_discos_pool(pool["id"])
                discos_pool = []
                for d in todos_los_disks:
                    if d.get("pool") == pool["name"]:
                        discos_pool.append({
                            "name": d.get("name"),
                            "type": d.get("type"),
                            "temperature": d.get("temperature"),
                            "smart_enabled": d.get("smart_enabled"),
                            "smart_status": d.get("smart_status", {}).get("passed"),
                        })

                pools_data.append({
                    "name": pool["name"],
                    "status": pool["status"],
                    "size": size,
                    "available": available,
                    "used_percent": used_percent,
                    "read_errors": read_errors,
                    "write_errors": write_errors,
                    "checksum_errors": checksum_errors,
                    "fragmentation": fragmentation,
                    "self_healed": self_healed,
                    "configured_ashift": configured_ashift,
                    "logical_ashift": logical_ashift,
                    "physical_ashift": physical_ashift,
                    "ops": ops,
                    "bytes": bytes_io,
                    "resilvering": pool.get("resilvering", False),
                    "disks": discos_pool
                })

    mostrar_estado_pipboy(pools_data)

    print("\nEspacio disponible para aplicaciones:")
    espacio_app = espacio_disponible_aplicaciones()
    print(f"  {espacio_app} GB")

    respuesta = input("\n¿Deseas guardar un backup de la configuración ahora? (s/n): ").strip().lower()
    if respuesta == "s":
        descargar_backup_config()