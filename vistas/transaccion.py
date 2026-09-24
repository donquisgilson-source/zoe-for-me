import flet as ft
import time
from datetime import datetime

# Importamos del cerebro para saber qué banco estamos usando y guardar los datos
from datos import ESTADO_APP, CUENTAS, MOVIMIENTOS, TASAS, guardar_datos

def vista_transaccion(page: ft.Page, cambiar_ruta):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    
    banco = ESTADO_APP["banco_activo"]
    
    # Prevención de errores si abren la ruta sin seleccionar banco
    if not banco:
        return ft.View("/transaccion", bgcolor=BG_COLOR)
        
    moneda_base = next(c["moneda"] for c in CUENTAS if c["banco"] == banco)
    es_ingreso = ESTADO_APP["trans_tipo"] == "ingreso"
    COLOR_TEMA = ft.colors.GREEN_400 if es_ingreso else ft.colors.RED_400
    
    cat_gasto = [ft.dropdown.Option(x) for x in ["Entretenimiento", "Servicios", "Comida", "Gasto Hormiga", "Salud"]]
    cat_ingreso = [ft.dropdown.Option(x) for x in ["Salario", "Ingresos Extras"]]

    txt_m = ft.TextField(label=f"Monto ({moneda_base})", color=TXT_PRINC, border_color=COLOR_TEMA, focused_border_color=COLOR_TEMA, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)
    dd_cat = ft.Dropdown(label="Categoría", options=cat_ingreso if es_ingreso else cat_gasto, border_color=CAJA_COLOR, color=TXT_PRINC)
    
    ui_tasa_usd = ft.Text("0.00 $", color=TXT_PRINC, size=16, weight=ft.FontWeight.BOLD)
    ui_tasa_eur = ft.Text("0.00 €", color=TXT_PRINC, size=16, weight=ft.FontWeight.BOLD)
    ui_tasa_usdt = ft.Text("0.00 ₮", color=TXT_PRINC, size=16, weight=ft.FontWeight.BOLD)

    def calcular_tasas_vuelo(e):
        if not txt_m.value:
            ui_tasa_usd.value = "0.00 $"; ui_tasa_eur.value = "0.00 €"; ui_tasa_usdt.value = "0.00 ₮"
            page.update(); return
        try:
            monto = float(txt_m.value.replace(",", "."))
            v_bs = monto if moneda_base == "Bs" else monto * TASAS["BCV"] if moneda_base == "USD" else monto * TASAS["USDT_COMPRA"]
            ui_tasa_usd.value = f"{v_bs/TASAS['BCV']:,.2f} $" if TASAS['BCV'] > 0 else "0.00 $"
            ui_tasa_eur.value = f"{v_bs/TASAS['EURO']:,.2f} €" if TASAS['EURO'] > 0 else "0.00 €"
            ui_tasa_usdt.value = f"{v_bs/TASAS['USDT_COMPRA']:,.2f} ₮" if TASAS['USDT_COMPRA'] > 0 else "0.00 ₮"
        except: pass
        page.update()
    txt_m.on_change = calcular_tasas_vuelo

    def cambiar_tab(e):
        ESTADO_APP["trans_tipo"] = "ingreso" if e.control.selected_index == 0 else "gasto"
        cambiar_ruta(None)

    tabs = ft.Tabs(selected_index=0 if es_ingreso else 1, on_change=cambiar_tab, tabs=[ft.Tab(text="Ingreso"), ft.Tab(text="Egreso")])

    def guardar_trans(e):
        if not txt_m.value or not dd_cat.value:
            page.open(ft.SnackBar(ft.Text("Llena todos los campos", color="#050505"), bgcolor="red")); return
        try:
            monto = float(txt_m.value.replace(",", "."))
            for c in CUENTAS:
                if c["banco"] == banco:
                    c["saldo_original"] += monto if es_ingreso else -monto
                    break
            tasa_del_dia = TASAS["BCV"]
            valor_usd_congelado = monto / tasa_del_dia if moneda_base == "Bs" else (monto * TASAS["USDT_COMPRA"]) / tasa_del_dia if moneda_base == "USDT" else monto 
            nuevo_id = int(time.time())
            icono_cat = ft.icons.ATTACH_MONEY if es_ingreso else ft.icons.SHOPPING_BAG
            
            MOVIMIENTOS.insert(0, {
                "id": nuevo_id, "banco": banco, "tipo": ESTADO_APP["trans_tipo"], "titulo": dd_cat.value, 
                "fecha": datetime.now().strftime("%d/%m/%Y"), "categoria": dd_cat.value, "monto": monto, 
                "icono": icono_cat, "tasa_historica": tasa_del_dia, "eq_usd": valor_usd_congelado
            })
            # Actualizamos el caché en el celular
            guardar_datos(page) 
            page.go("/")
        except ValueError: pass

    recuadro_tasas = ft.Container(
        content=ft.Row([
            ft.Column([ft.Text("Eq. USD BCV", color=TXT_SECUN, size=11), ui_tasa_usd], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("Eq. EURO", color=TXT_SECUN, size=11), ui_tasa_eur], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Column([ft.Text("Eq. USDT P2P", color=TXT_SECUN, size=11), ui_tasa_usdt], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        bgcolor=CAJA_COLOR, padding=15, border_radius=10, border=ft.border.all(1, COLOR_TEMA)
    )

    return ft.View("/transaccion", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
        ft.Container(height=3, bgcolor=COLOR_TEMA, border_radius=2),
        ft.AppBar(title=ft.Text(banco, color=COLOR_TEMA), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_TEMA, on_click=lambda _: page.go("/"))),
        tabs, ft.Container(height=10), txt_m, dd_cat, ft.Container(height=10), recuadro_tasas, ft.Container(expand=True),
        ft.ElevatedButton("GUARDAR MOVIMIENTO", color="#050505" if es_oscuro else ft.colors.WHITE, bgcolor=COLOR_TEMA, height=60, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=guardar_trans)
    ])