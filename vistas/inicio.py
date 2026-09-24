import flet as ft
import threading
from datos import ESTADO_APP, CUENTAS, TASAS, BANCOS_DISPONIBLES, guardar_datos
from servicios import actualizar_saldo_binance

def vista_inicio(page: ft.Page, cambiar_ruta, ui_fecha_tiempo):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    COLOR_DORADO = "#D4AF37"
    logo_actual = "mandy_logo.png" if es_oscuro else "zoe_logo.jpg"

    def cambiar_tema(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        cambiar_ruta(None)

    def cambiar_moneda_vista(e, nueva_moneda):
        ESTADO_APP["moneda_vista"] = nueva_moneda
        cambiar_ruta(None) 

    def ir_transaccion(tipo, banco):
        ESTADO_APP["trans_tipo"] = tipo
        ESTADO_APP["banco_activo"] = banco
        page.go("/transaccion")

    def ir_editar(banco):
        ESTADO_APP["banco_activo"] = banco
        page.go("/editar")

    def ir_historial(banco):
        ESTADO_APP["banco_activo"] = banco
        page.go("/historial")

    dd_nuevo_banco = ft.Dropdown(label="Selecciona un Banco", options=[ft.dropdown.Option(b) for b in BANCOS_DISPONIBLES.keys()], border_color=COLOR_DORADO)
    dd_nueva_moneda = ft.Dropdown(label="Moneda", options=[ft.dropdown.Option("Bs"), ft.dropdown.Option("USD"), ft.dropdown.Option("USDT")], value="Bs", border_color=COLOR_DORADO)
    txt_nuevo_saldo = ft.TextField(label="Saldo Inicial", value="0", border_color=COLOR_DORADO, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)

    def guardar_nuevo_banco(e):
        if not dd_nuevo_banco.value:
            page.open(ft.SnackBar(ft.Text("Selecciona un banco", color="#050505"), bgcolor="red")); return
        if any(c["banco"] == dd_nuevo_banco.value for c in CUENTAS):
            page.open(ft.SnackBar(ft.Text("Este banco ya está registrado", color="#050505"), bgcolor="red")); return

        try: saldo = float(txt_nuevo_saldo.value.replace(",", "."))
        except ValueError: saldo = 0.0

        CUENTAS.append({"banco": dd_nuevo_banco.value, "saldo_original": saldo, "moneda": dd_nueva_moneda.value, "logo": BANCOS_DISPONIBLES[dd_nuevo_banco.value]})
        guardar_datos(page)
        page.close(dialog_agregar)
        cambiar_ruta(None)
        page.open(ft.SnackBar(ft.Text("Banco agregado con éxito", color="#050505"), bgcolor=COLOR_DORADO))

    dialog_agregar = ft.AlertDialog(
        bgcolor="#1A1A1A", title=ft.Text("Agregar Nueva Cuenta", color=COLOR_DORADO, weight=ft.FontWeight.BOLD),
        content=ft.Column([dd_nuevo_banco, dd_nueva_moneda, txt_nuevo_saldo], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dialog_agregar)),
            ft.ElevatedButton("Agregar", bgcolor=COLOR_DORADO, color="#050505", on_click=guardar_nuevo_banco)
        ]
    )

    total_acum = total_bs = total_usd = 0.0
    lista_bancos_ui = []
    
    for cuenta in CUENTAS:
        if ESTADO_APP["moneda_vista"] == "Original":
            saldo_mostrar = cuenta["saldo_original"]
            if cuenta["moneda"] == "Bs": simbolo = "Bs "; total_bs += saldo_mostrar
            elif cuenta["moneda"] == "USD": simbolo = "$ "; total_usd += saldo_mostrar
            elif cuenta["moneda"] == "USDT": simbolo = "₮ "; total_usd += saldo_mostrar 
        else:
            v_bs = cuenta["saldo_original"] if cuenta["moneda"] == "Bs" else cuenta["saldo_original"] * TASAS["BCV"] if cuenta["moneda"] == "USD" else cuenta["saldo_original"] * TASAS["USDT_COMPRA"]
            if ESTADO_APP["moneda_vista"] == "Bs.": saldo_mostrar = v_bs; simbolo = "Bs "
            elif ESTADO_APP["moneda_vista"] == "$ BCV": saldo_mostrar = v_bs / TASAS["BCV"] if TASAS["BCV"] > 0 else 0; simbolo = "$ "
            elif ESTADO_APP["moneda_vista"] == "€ BCV": saldo_mostrar = v_bs / TASAS["EURO"] if TASAS["EURO"] > 0 else 0; simbolo = "€ "
            elif ESTADO_APP["moneda_vista"] == "USDT": saldo_mostrar = v_bs / TASAS["USDT_COMPRA"] if TASAS["USDT_COMPRA"] > 0 else 0; simbolo = "₮ "
            total_acum += saldo_mostrar

        botones = []
        if cuenta["banco"] != "Binance":
            botones.append(ft.IconButton(ft.icons.ADD_CIRCLE_OUTLINE, icon_color=COLOR_DORADO, icon_size=22, tooltip="Ingreso", on_click=lambda e, b=cuenta["banco"]: ir_transaccion("ingreso", b)))
            botones.append(ft.IconButton(ft.icons.REMOVE_CIRCLE_OUTLINE, icon_color=COLOR_DORADO, icon_size=22, tooltip="Egreso", on_click=lambda e, b=cuenta["banco"]: ir_transaccion("gasto", b)))
        else:
            # ---> NUEVO BOTÓN REFRESCAR SOLO PARA BINANCE EN EL INICIO <---
            def click_refresh_binance(e):
                page.open(ft.SnackBar(ft.Text("Sincronizando Binance...", color="#050505"), bgcolor=COLOR_DORADO))
                def bg_sync():
                    exito, msg = actualizar_saldo_binance(page)
                    if exito: cambiar_ruta(None)
                    else: 
                        page.open(ft.SnackBar(ft.Text(msg, color="white"), bgcolor="red"))
                        page.update()
                threading.Thread(target=bg_sync, daemon=True).start()
            
            botones.append(ft.IconButton(ft.icons.REFRESH, icon_color=COLOR_DORADO, icon_size=22, tooltip="Actualizar Saldo", on_click=click_refresh_binance))

        botones.append(ft.IconButton(ft.icons.EDIT, icon_color=COLOR_DORADO, icon_size=22, tooltip="Editar Cuenta", on_click=lambda e, b=cuenta["banco"]: ir_editar(b)))

        lista_bancos_ui.append(
            ft.Container(
                bgcolor=CAJA_COLOR,
                content=ft.ListTile(
                    leading=ft.Image(src=cuenta["logo"], width=40, height=40, fit=ft.ImageFit.CONTAIN),
                    title=ft.Text(cuenta["banco"], color=TXT_PRINC, weight=ft.FontWeight.W_500),
                    subtitle=ft.Text(f"{simbolo}{saldo_mostrar:,.2f}", color=COLOR_DORADO, size=16, weight=ft.FontWeight.BOLD),
                    trailing=ft.Row(botones, spacing=0, tight=True)
                ),
                on_click=lambda e, b=cuenta["banco"]: ir_historial(b),
                border_radius=10, ink=True 
            )
        )

    btn_agregar_banco = ft.Container(
        content=ft.ElevatedButton("+ AGREGAR BANCO", color=COLOR_DORADO, bgcolor=BG_COLOR, on_click=lambda _: page.open(dialog_agregar)),
        alignment=ft.alignment.center, padding=ft.padding.only(top=10, bottom=5)
    )

    btn_pago_movil = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row([ft.Icon(ft.icons.MOBILE_FRIENDLY, color="#050505"), ft.Text("COBRAR PAGO MÓVIL", color="#050505", weight=ft.FontWeight.BOLD, size=14)], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=COLOR_DORADO,
            height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            on_click=lambda _: page.go("/pagomovil")
        ),
        padding=ft.padding.only(top=5, bottom=10)
    )

    texto_tasa_global = ""
    if ESTADO_APP["moneda_vista"] == "$ BCV": texto_tasa_global = f"Tasa: {TASAS['BCV']:,.2f} Bs"
    elif ESTADO_APP["moneda_vista"] == "€ BCV": texto_tasa_global = f"Tasa: {TASAS['EURO']:,.2f} Bs"
    elif ESTADO_APP["moneda_vista"] == "USDT": texto_tasa_global = f"Tasa: {TASAS['USDT_COMPRA']:,.2f} Bs"

    ui_mis_cuentas = ft.Row([ft.Text("Mis Cuentas", color=TXT_PRINC, size=18, weight=ft.FontWeight.BOLD), ft.Text(texto_tasa_global, color=COLOR_DORADO, size=16, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    if ESTADO_APP["moneda_vista"] == "Original":
        ui_gran_saldo = ft.Column([
            ft.Text("SALDO ORIGINAL", color=TXT_SECUN, size=14),
            ft.Text(f"Bs {total_bs:,.2f}", color=COLOR_DORADO, size=32, weight=ft.FontWeight.BOLD),
            ft.Text(f"$ {total_usd:,.2f}", color=COLOR_DORADO, size=32, weight=ft.FontWeight.BOLD),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        simbolo_total = "Bs" if ESTADO_APP["moneda_vista"] == "Bs." else "€" if ESTADO_APP["moneda_vista"] == "€ BCV" else "$" if ESTADO_APP["moneda_vista"] == "$ BCV" else "₮"
        ui_gran_saldo = ft.Column([
            ft.Text("SALDO TOTAL", color=TXT_SECUN, size=14),
            ft.Text(f"{simbolo_total} {total_acum:,.2f}", color=COLOR_DORADO, size=46, weight=ft.FontWeight.BOLD),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    return ft.View("/", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
        ft.Column([
            ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2, margin=ft.margin.only(bottom=10)),
            ft.Row([
                ft.Row([
                    ft.Container(content=ft.Image(src=logo_actual, width=40, height=40, fit=ft.ImageFit.CONTAIN), border_radius=10, clip_behavior=ft.ClipBehavior.HARD_EDGE),
                    ft.Text("Zoe For Me", size=24, weight=ft.FontWeight.BOLD, italic=True, color=COLOR_DORADO)
                ], spacing=10),
                ft.IconButton(ft.icons.LIGHT_MODE if es_oscuro else ft.icons.DARK_MODE, icon_color=COLOR_DORADO, on_click=cambiar_tema)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], spacing=0), 
        ft.Container(height=10), ui_fecha_tiempo,
        ft.Container(content=ui_gran_saldo, alignment=ft.alignment.center, padding=ft.padding.symmetric(vertical=15)),
        ft.Row([ft.ElevatedButton(n, color=BG_COLOR if ESTADO_APP["moneda_vista"] == n else TXT_PRINC, bgcolor=COLOR_DORADO if ESTADO_APP["moneda_vista"] == n else CAJA_COLOR, on_click=lambda e, nx=n: cambiar_moneda_vista(e, nx), style=ft.ButtonStyle(padding=5)) for n in ["Original", "Bs.", "$ BCV", "€ BCV", "USDT"]], alignment=ft.MainAxisAlignment.CENTER, spacing=5),
        ft.Divider(color=TXT_SECUN, height=30), ui_mis_cuentas, ft.Column(lista_bancos_ui, spacing=5), 
        btn_agregar_banco, 
        btn_pago_movil, 
        ft.Container(expand=True),
        ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.CALCULATE, color="#050505"), ft.Text("CALCULADORA", color="#050505", weight=ft.FontWeight.BOLD, size=16)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_DORADO, height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=lambda _: page.go("/calculadora"))
    ])