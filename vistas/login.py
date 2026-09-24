import flet as ft
import time
import threading
from datos import ESTADO_APP

def vista_login(page: ft.Page):
    COLOR_DORADO = "#D4AF37"
    
    pin_guardado = page.client_storage.get("zoe_pin")
    estado = {"fase": "login" if pin_guardado else "crear", "pin_temp": ""}
    
    txt_titulo = ft.Text(
        "Ingresa tu PIN" if pin_guardado else "Crea un PIN de 4 dígitos", 
        color=COLOR_DORADO, size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER
    )
    
    txt_subtitulo = ft.Text(
        "Zoe For Me" if pin_guardado else "Protege tu información financiera", 
        color=ft.colors.WHITE70, size=14, text_align=ft.TextAlign.CENTER
    )
    
    txt_pin = ft.TextField(
        password=True, 
        text_align=ft.TextAlign.CENTER,
        width=200,
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=COLOR_DORADO,
        focused_border_color=COLOR_DORADO,
        color=ft.colors.WHITE,
        max_length=4,
    )

    def verificar_pin(e):
        val = txt_pin.value
        if len(val) != 4:
            page.open(ft.SnackBar(ft.Text("El PIN debe tener 4 dígitos", color="#050505"), bgcolor="red"))
            return
            
        if estado["fase"] == "login":
            if val == pin_guardado:
                ESTADO_APP["autenticado"] = True  # <--- Abrimos el candado
                page.go("/") 
            else:
                page.open(ft.SnackBar(ft.Text("PIN Incorrecto", color="#050505", weight=ft.FontWeight.BOLD), bgcolor="red"))
                txt_pin.value = ""
                page.update()
        elif estado["fase"] == "crear":
            estado["pin_temp"] = val
            estado["fase"] = "confirmar"
            txt_titulo.value = "Confirma tu PIN"
            txt_subtitulo.value = "Escríbelo de nuevo"
            txt_pin.value = ""
            page.update()
        elif estado["fase"] == "confirmar":
            if val == estado["pin_temp"]:
                page.client_storage.set("zoe_pin", val)
                ESTADO_APP["autenticado"] = True  # <--- Abrimos el candado
                page.open(ft.SnackBar(ft.Text("PIN configurado con éxito", color="#050505"), bgcolor=ft.colors.GREEN_400))
                page.go("/")
            else:
                page.open(ft.SnackBar(ft.Text("Los PIN no coinciden. Intenta de nuevo.", color="#050505"), bgcolor="red"))
                estado["fase"] = "crear"
                txt_titulo.value = "Crea un PIN de 4 dígitos"
                txt_subtitulo.value = "Protege tu información financiera"
                txt_pin.value = ""
                page.update()

    txt_pin.on_submit = verificar_pin

    btn_entrar = ft.ElevatedButton(
        "ENTRAR", 
        bgcolor=COLOR_DORADO, 
        color="#050505", 
        width=200,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=verificar_pin
    )

    btn_calc = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.icons.CALCULATE, color="#050505"), ft.Text("CALCULADORA", color="#050505", weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER), 
        bgcolor=COLOR_DORADO, 
        height=50,
        width=300,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=25)), 
        on_click=lambda _: page.go("/calculadora")
    )

    # La caja semitransparente que contiene todo
    caja_interactiva = ft.Container(
        content=ft.Column([
            txt_titulo, 
            txt_subtitulo,
            ft.Container(height=10),
            txt_pin,
            btn_entrar,
            ft.Container(height=40),
            btn_calc
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#CC000000", # Semitransparente oscuro
        padding=30,
        border_radius=20,
        width=350,
        visible=False # <--- EMPIEZA OCULTA
    )

    # Hilo que espera 1 segundo y luego muestra la caja del PIN
    def revelar_interfaz():
        time.sleep(1) # Tiempo exacto que pidiste
        caja_interactiva.visible = True
        page.update()
        
    threading.Thread(target=revelar_interfaz, daemon=True).start()

    return ft.View(
        "/login",
        padding=0, 
        controls=[
            ft.Container(
                image_src="inicio_zoe.jpg",
                image_fit=ft.ImageFit.COVER,
                expand=True,
                alignment=ft.alignment.center,
                content=caja_interactiva # Se revelará aquí adentro
            )
        ]
    )