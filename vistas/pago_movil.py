import flet as ft
from datos import TASAS, CODIGOS_PAGO_MOVIL

def vista_pago_movil(page: ft.Page):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    COLOR_DORADO = "#D4AF37"

    b_pm = page.client_storage.get("pm_banco") or ""
    t_pm = page.client_storage.get("pm_telefono") or ""
    c_pm = page.client_storage.get("pm_cedula") or ""

    dd_pm_banco = ft.Dropdown(label="Tu Banco", value=b_pm if b_pm in CODIGOS_PAGO_MOVIL else None, options=[ft.dropdown.Option(b) for b in CODIGOS_PAGO_MOVIL], border_color=COLOR_DORADO, color=TXT_PRINC)
    txt_pm_telefono = ft.TextField(label="Tu Teléfono (Ej: 04141234567)", value=t_pm, border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, keyboard_type=ft.KeyboardType.PHONE)
    txt_pm_cedula = ft.TextField(label="Tu Cédula (Ej: V12345678)", value=c_pm, border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC)
    
    txt_pm_monto_bs = ft.TextField(label="Monto en Bolívares (Bs)", border_color=COLOR_DORADO, focused_border_color=COLOR_DORADO, color=TXT_PRINC, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)
    txt_pm_monto_usd = ft.TextField(label="Monto en Dólares ($)", border_color=ft.colors.GREEN_400, focused_border_color=ft.colors.GREEN_400, color=TXT_PRINC, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)

    def calc_pm_bs(e):
        if txt_pm_monto_bs.value:
            try:
                monto = float(txt_pm_monto_bs.value.replace(",", "."))
                txt_pm_monto_usd.value = f"{monto / TASAS['BCV']:.2f}".replace(".", ",") if TASAS['BCV'] > 0 else ""
            except: pass
        else: txt_pm_monto_usd.value = ""
        page.update()

    def calc_pm_usd(e):
        if txt_pm_monto_usd.value:
            try:
                monto = float(txt_pm_monto_usd.value.replace(",", "."))
                txt_pm_monto_bs.value = f"{monto * TASAS['BCV']:.2f}".replace(".", ",")
            except: pass
        else: txt_pm_monto_bs.value = ""
        page.update()

    txt_pm_monto_bs.on_change = calc_pm_bs
    txt_pm_monto_usd.on_change = calc_pm_usd

    def copiar_pago_movil(e):
        if not dd_pm_banco.value or not txt_pm_telefono.value or not txt_pm_cedula.value or not txt_pm_monto_bs.value:
            page.open(ft.SnackBar(ft.Text("Completa todos los campos primero.", color="#050505"), bgcolor="red")); return
        
        page.client_storage.set("pm_banco", dd_pm_banco.value)
        page.client_storage.set("pm_telefono", txt_pm_telefono.value)
        page.client_storage.set("pm_cedula", txt_pm_cedula.value)

        codigo = dd_pm_banco.value.split(" - ")[0]
        monto_final = txt_pm_monto_bs.value.replace(".", ",")

        texto_copiar = f"{codigo}\n{txt_pm_telefono.value}\n{txt_pm_cedula.value}\n{monto_final}"
        
        page.set_clipboard(texto_copiar)
        page.open(ft.SnackBar(ft.Text("¡Datos copiados! Listos para pegar.", color="#050505", weight=ft.FontWeight.BOLD), bgcolor=ft.colors.GREEN_400))

    return ft.View("/pagomovil", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
        ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2),
        ft.AppBar(title=ft.Text("Cobrar Pago Móvil", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
        ft.Text("Tus Datos (Se guardan automáticamente)", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
        dd_pm_banco, txt_pm_telefono, txt_pm_cedula,
        ft.Divider(color=TXT_SECUN, height=30),
        ft.Text("¿Cuánto vas a cobrar?", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
        txt_pm_monto_usd, 
        txt_pm_monto_bs,
        ft.Container(expand=True),
        ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.COPY, color="#050505"), ft.Text("COPIAR DATOS", color="#050505", weight=ft.FontWeight.BOLD, size=16)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_DORADO, height=60, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=copiar_pago_movil)
    ])