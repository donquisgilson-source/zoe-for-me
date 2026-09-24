import flet as ft
import threading 
import time      
from datetime import datetime, timedelta

from datos import *
from servicios import *
from vistas.inicio import vista_inicio
from vistas.calculadora import vista_calculadora
from vistas.pago_movil import vista_pago_movil 
from vistas.transaccion import vista_transaccion
from vistas.editar import vista_editar
from vistas.historial import vista_historial
from vistas.login import vista_login

def main(page: ft.Page):
    inicializar_datos(page)

    page.title = "Zoe For Me"
    page.window_width = 400
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.DARK
    
    COLOR_NEGRO_PURO = "#050505" 
    COLOR_DORADO = "#D4AF37"

    def viajar_tiempo(direccion):
        fecha_actual_str = ESTADO_APP["fecha_bcv"]
        try:
            obj_fecha = datetime.strptime(fecha_actual_str, "%d/%m/%Y")
            if direccion == "atras": nueva_fecha = obj_fecha - timedelta(days=1)
            else: nueva_fecha = obj_fecha + timedelta(days=1)
                
            nueva_fecha_str = nueva_fecha.strftime("%d/%m/%Y")
            
            if nueva_fecha_str in HISTORIAL_TASAS:
                ESTADO_APP["fecha_bcv"] = nueva_fecha_str
                TASAS.update(HISTORIAL_TASAS[nueva_fecha_str])
                cambiar_ruta(None)
            else:
                page.open(ft.SnackBar(ft.Text(f"No tienes tasas guardadas del {nueva_fecha_str}", color="#050505", weight=ft.FontWeight.BOLD), bgcolor=COLOR_DORADO))
        except Exception: pass

    def bucle_sincronizacion():
        while True:
            time.sleep(300) 
            obtener_tasas_red(page)
            actualizar_saldo_binance(page)
            if page.route in ["/", "/transaccion", "/calculadora"]:
                cambiar_ruta(None)

    def cambiar_fecha_inicio(e):
        if dp_inicio.value: ESTADO_APP["fecha_inicio"] = dp_inicio.value.strftime("%d/%m/%Y"); cambiar_ruta(None)
    def cambiar_fecha_fin(e):
        if dp_fin.value: ESTADO_APP["fecha_fin"] = dp_fin.value.strftime("%d/%m/%Y"); cambiar_ruta(None)

    dp_inicio = ft.DatePicker(first_date=datetime(2020, 1, 1), last_date=datetime(2050, 12, 31), on_change=cambiar_fecha_inicio)
    dp_fin = ft.DatePicker(first_date=datetime(2020, 1, 1), last_date=datetime(2050, 12, 31), on_change=cambiar_fecha_fin)
    page.overlay.extend([dp_inicio, dp_fin])

    def cambiar_ruta(e):
        es_oscuro = page.theme_mode == ft.ThemeMode.DARK
        TXT_PRINC = ft.colors.WHITE if es_oscuro else COLOR_NEGRO_PURO

        page.views.clear()

        ui_fecha_tiempo = ft.Row([
            ft.IconButton(ft.icons.ARROW_BACK_IOS, icon_color=COLOR_DORADO, icon_size=16, on_click=lambda _: viajar_tiempo("atras")),
            ft.Text(f"BCV: {ESTADO_APP['fecha_bcv']}", color=TXT_PRINC, size=14, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.icons.ARROW_FORWARD_IOS, icon_color=COLOR_DORADO, icon_size=16, on_click=lambda _: viajar_tiempo("futuro")),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)

        # RUTAS DE LA APP
        if page.route == "/login": page.views.append(vista_login(page))
        elif page.route == "/": page.views.append(vista_inicio(page, cambiar_ruta, ui_fecha_tiempo))
        elif page.route == "/pagomovil": page.views.append(vista_pago_movil(page))
        elif page.route == "/calculadora": page.views.append(vista_calculadora(page, ui_fecha_tiempo))
        elif page.route == "/transaccion": page.views.append(vista_transaccion(page, cambiar_ruta))
        elif page.route == "/editar": page.views.append(vista_editar(page, cambiar_ruta))
        elif page.route == "/historial": page.views.append(vista_historial(page, cambiar_ruta, dp_inicio, dp_fin))
        
        page.update()

    def regresar(e):
        if not ESTADO_APP.get("autenticado"):
            page.go("/login") # Bloqueo absoluto si no hay llave
        else:
            page.go("/")      # Vuelve al inicio si ya entraste

    page.on_route_change = cambiar_ruta
    page.on_view_pop = regresar
    
    # --- ARRANQUE DIRECTO ---
    def iniciar_red():
        obtener_tasas_red(page)
        actualizar_saldo_binance(page)
        bucle_sincronizacion()

    # Empezamos a descargar los datos en segundo plano mientras el usuario ve la imagen
    threading.Thread(target=iniciar_red, daemon=True).start()
    page.go("/login") 

ft.app(target=main, assets_dir="assets")