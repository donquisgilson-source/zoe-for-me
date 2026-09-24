import flet as ft
import threading
from datos import ESTADO_APP, CUENTAS, MOVIMIENTOS, API_KEYS, guardar_datos
from servicios import actualizar_saldo_binance

def vista_editar(page: ft.Page, cambiar_ruta):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    COLOR_DORADO = "#D4AF37"
    
    banco = ESTADO_APP["banco_activo"]
    
    # Previene errores si no hay banco seleccionado
    if not banco:
        return ft.View("/editar", bgcolor=BG_COLOR)

    # --- LÓGICA DE ELIMINAR BANCO ---
    def confirmar_eliminar_banco(e):
        CUENTAS[:] = [c for c in CUENTAS if c["banco"] != banco]
        MOVIMIENTOS[:] = [m for m in MOVIMIENTOS if m["banco"] != banco]
        guardar_datos(page)
        
        page.close(dialog_eliminar)
        page.open(ft.SnackBar(ft.Text(f"{banco} eliminado", color=ft.colors.WHITE), bgcolor=ft.colors.RED_700))
        page.go("/")

    dialog_eliminar = ft.AlertDialog(
        title=ft.Text("⚠️ Advertencia", color=ft.colors.RED_400, weight=ft.FontWeight.BOLD),
        content=ft.Text("¿Estás seguro de eliminar esta cuenta? Se borrará todo su historial y saldos asociados permanentemente."),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dialog_eliminar)),
            ft.ElevatedButton("Sí, Eliminar", bgcolor=ft.colors.RED_700, color=ft.colors.WHITE, on_click=confirmar_eliminar_banco)
        ]
    )
    # --------------------------------

    controles_editar = [
        ft.AppBar(title=ft.Text(f"Configurar {banco}", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
    ]

    if banco == "Binance":
        def guardar_api(e):
            page.client_storage.set("binance_key", txt_api_key_ed.value)
            page.client_storage.set("binance_secret", txt_api_secret_ed.value)
            API_KEYS["binance_key"] = txt_api_key_ed.value
            API_KEYS["binance_secret"] = txt_api_secret_ed.value
            page.open(ft.SnackBar(ft.Text("Sincronizando con Binance...", color="#050505"), bgcolor=COLOR_DORADO))
            # Sincronizamos en segundo plano
            threading.Thread(target=lambda: [actualizar_saldo_binance(page), cambiar_ruta(None)], daemon=True).start()
            page.go("/")
            
        txt_api_key_ed = ft.TextField(label="API Key (Lectura)", password=True, border_color=COLOR_DORADO, value=API_KEYS.get("binance_key", ""))
        txt_api_secret_ed = ft.TextField(label="Secret Key (Lectura)", password=True, border_color=COLOR_DORADO, value=API_KEYS.get("binance_secret", ""))
        
        controles_editar.extend([
            ft.Text("Sincronización Automática (API Binance):", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
            ft.Text("Tus llaves se guardan encriptadas en este dispositivo. Esto actualiza tu saldo y transacciones P2P automáticamente.", color=TXT_SECUN, size=11),
            txt_api_key_ed, txt_api_secret_ed,
            ft.ElevatedButton("GUARDAR Y SINCRONIZAR API", color="#050505", bgcolor=COLOR_DORADO, width=400, on_click=guardar_api)
        ])
    else:
        # Para bancos normales, extraemos el saldo actual
        saldo_actual = next((c["saldo_original"] for c in CUENTAS if c["banco"] == banco), 0.0)
        txt_nuevo = ft.TextField(label="Nuevo Saldo Manual", value=str(saldo_actual), color=TXT_PRINC, border_color=COLOR_DORADO, keyboard_type=ft.KeyboardType.NUMBER)
        
        def guardar_edicion(e):
            try:
                monto = float(txt_nuevo.value.replace(",", "."))
                for c in CUENTAS:
                    if c["banco"] == banco: 
                        c["saldo_original"] = monto
                        break
                guardar_datos(page)
                page.go("/")
            except ValueError: 
                pass
        
        controles_editar.extend([
            ft.Text("1. Ajuste Manual de Saldo:", color=TXT_PRINC, weight=ft.FontWeight.BOLD), txt_nuevo,
            ft.ElevatedButton("ACTUALIZAR MANUALMENTE", color="#050505", bgcolor=COLOR_DORADO, width=400, on_click=guardar_edicion),
            ft.Container(expand=True), 
            ft.ElevatedButton("ELIMINAR CUENTA", color=ft.colors.WHITE, bgcolor=ft.colors.RED_700, width=400, on_click=lambda _: page.open(dialog_eliminar))
        ])

    return ft.View("/editar", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=controles_editar)