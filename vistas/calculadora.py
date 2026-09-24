import flet as ft
from datos import TASAS, ESTADO_APP  # <--- Agregamos ESTADO_APP aquí

def vista_calculadora(page: ft.Page, ui_fecha_tiempo):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    COLOR_DORADO = "#D4AF37"

    def calcular_inputs(e):
        if not e.control.value:
            txt_bs.value = txt_dolar.value = txt_euro.value = txt_usdt_c.value = txt_usdt_v.value = ""
            page.update(); return
        try:
            m = float(e.control.value.replace(",", "."))
            bs = m if e.control == txt_bs else m * TASAS["BCV"] if e.control == txt_dolar else m * TASAS["EURO"] if e.control == txt_euro else m * TASAS["USDT_COMPRA"] if e.control == txt_usdt_c else m * TASAS["USDT_VENTA"]
            if e.control != txt_bs: txt_bs.value = f"{bs:,.2f}"
            if e.control != txt_dolar: txt_dolar.value = f"{bs/TASAS['BCV'] if TASAS['BCV']>0 else 0:,.2f}"
            if e.control != txt_euro: txt_euro.value = f"{bs/TASAS['EURO'] if TASAS['EURO']>0 else 0:,.2f}"
            if e.control != txt_usdt_c: txt_usdt_c.value = f"{bs/TASAS['USDT_COMPRA'] if TASAS['USDT_COMPRA']>0 else 0:,.2f}"
            if e.control != txt_usdt_v: txt_usdt_v.value = f"{bs/TASAS['USDT_VENTA'] if TASAS['USDT_VENTA']>0 else 0:,.2f}"
        except ValueError: pass
        page.update()

    filtro = ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$")
    txt_bs = ft.TextField(label="Bolívares (Bs)", border_color=COLOR_DORADO, focused_border_color=COLOR_DORADO, color=TXT_PRINC, on_change=calcular_inputs, input_filter=filtro)
    txt_dolar = ft.TextField(label="Dólar BCV", border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, on_change=calcular_inputs, input_filter=filtro)
    txt_euro = ft.TextField(label="Euro BCV", border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, on_change=calcular_inputs, input_filter=filtro)
    txt_usdt_c = ft.TextField(label="USDT Binance (Compra)", border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, on_change=calcular_inputs, input_filter=filtro)
    txt_usdt_v = ft.TextField(label="USDT Binance (Venta)", border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, on_change=calcular_inputs, input_filter=filtro)

    b_bs = TASAS["USDT_COMPRA"] - TASAS["BCV"]; b_pct = (b_bs / TASAS["BCV"] * 100) if TASAS["BCV"] > 0 else 0
    
    # --- LA CORRECCIÓN DE LA FLECHA ATRÁS ESTÁ AQUÍ ---
    btn_atras = ft.IconButton(
        ft.icons.ARROW_BACK, 
        icon_color=COLOR_DORADO, 
        on_click=lambda _: page.go("/") if ESTADO_APP.get("autenticado") else page.go("/login")
    )

    return ft.View("/calculadora", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
        ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2, margin=ft.margin.only(bottom=10)),
        ft.AppBar(title=ft.Text("Mercado", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=btn_atras),
        ui_fecha_tiempo, ft.Container(height=10),
        ft.Row([
            ft.Column([ft.Text("BCV", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['BCV']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("EURO", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['EURO']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("P2P COM", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['USDT_COMPRA']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("P2P VEN", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['USDT_VENTA']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(color=TXT_SECUN, height=30), txt_bs, txt_dolar, txt_euro, txt_usdt_c, txt_usdt_v,
        ft.Container(content=ft.Text(f"Diferencia USDT y $ BCV = {b_pct:.2f}% ({b_bs:,.2f} Bs)", color=COLOR_DORADO, size=15, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center, padding=10)
    ])