import flet as ft
import ssl
import requests
import threading 
import time      
from datetime import datetime, timedelta
import hmac
import hashlib

ssl._create_default_https_context = ssl._create_unverified_context
import urllib3
urllib3.disable_warnings() 

def main(page: ft.Page):
    page.title = "Zoe For Me"
    page.window_width = 400
    page.window_height = 750
    page.theme_mode = ft.ThemeMode.DARK
    
    COLOR_NEGRO_PURO = "#050505" 
    COLOR_DORADO = "#D4AF37"

    TASAS = {
        "BCV": 849.56,
        "EURO": 974.00,
        "USDT_COMPRA": 950.00,
        "USDT_VENTA": 940.00
    }
    
    API_KEYS = {
        "binance_key": page.client_storage.get("binance_key") or "",
        "binance_secret": page.client_storage.get("binance_secret") or ""
    }
    
    ESTADO_APP = {
        "moneda_vista": "Original",
        "fecha_bcv": "Válida para el Lunes" if datetime.now().weekday() in [5, 6] else datetime.now().strftime("%d/%m/%Y"),
        "trans_tipo": "ingreso",  
        "banco_activo": "",
        "fecha_inicio": datetime.now().replace(day=1).strftime("%d/%m/%Y"), 
        "fecha_fin": datetime.now().strftime("%d/%m/%Y"), 
        "movimiento_seleccionado": None
    }

    # ==========================================
    # PERSISTENCIA Y DATOS
    # ==========================================
    cuentas_guardadas = page.client_storage.get("zoe_cuentas")
    if cuentas_guardadas: CUENTAS = cuentas_guardadas
    else:
        CUENTAS = [
            {"banco": "Banco Mercantil", "saldo_original": 0.0, "moneda": "Bs", "logo": "mercantil.png"},
            {"banco": "Banco de Venezuela", "saldo_original": 0.0, "moneda": "Bs", "logo": "bancodevenezuela.png"},
            {"banco": "Binance", "saldo_original": 0.0, "moneda": "USDT", "logo": "binance.png"},
            {"banco": "Divisas Físicas", "saldo_original": 0.0, "moneda": "USD", "logo": "divisas.png"}
        ]

    movs_guardados = page.client_storage.get("zoe_movimientos")
    MOVIMIENTOS = movs_guardados if movs_guardados else []

    def guardar_datos():
        page.client_storage.set("zoe_cuentas", CUENTAS)
        page.client_storage.set("zoe_movimientos", MOVIMIENTOS)

    BANCOS_DISPONIBLES = {
        "Banesco": "banesco.png", "BBVA Provincial": "provincial.png", "BNC": "bnc.png",
        "Bancamiga": "bancamiga.png","Banco Digital de los Trabajadores": "bdt.png", "Banco Bicentenario": "bicentenario.png",
        "Banco del Tesoro": "tesoro.png", "Bancaribe": "bancaribe.png",
        "Banco Exterior": "exterior.png","Humaniz Banco": "humanizmain.png","Humaniz Alimentación": "Humanizalim.png", "Banco Activo": "activo.png",
        "Banplus": "banplus.png", "Banco Plaza": "plaza.png", "100% Banco": "cienporciento.png",
        "Zinli": "zinli.png","Zelle": "Zelle.png", "Wally": "wally.png", "Efectivo (Bs)": "efectivobs.png"
    }

    CODIGOS_PAGO_MOVIL = [
        "0102 - Banco de Venezuela", "0104 - Venezolano de Crédito", "0105 - Mercantil", 
        "0108 - Provincial", "0114 - Bancaribe", "0115 - Banco Exterior", 
        "0128 - Banco Caroní", "0134 - Banesco", "0138 - Banco Plaza", 
        "0146 - Bangente", "0151 - BFC", "0156 - 100% Banco", "0157 - Del Sur",
        "0163 - Banco del Tesoro", "0166 - Banco Agrícola", "0168 - Bancrecer", 
        "0169 - Mi Banco", "0171 - Banco Activo", "0172 - Bancamiga", 
        "0173 - Banco Int. de Desarrollo", "0174 - Banplus", "0175 - Bicentenario", 
        "0177 - Banfanb", "0191 - BNC"
    ]

    # ==========================================
    # LÓGICAS GENERALES Y RED
    # ==========================================
    def cambiar_tema(e):
        page.theme_mode = ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK else ft.ThemeMode.DARK
        cambiar_ruta(None)

    def viajar_tiempo(direccion):
        page.open(ft.SnackBar(ft.Text("Buscando histórico de tasas (En desarrollo)", color=COLOR_NEGRO_PURO, weight=ft.FontWeight.BOLD), bgcolor=COLOR_DORADO))

    def actualizar_saldo_binance():
        if not API_KEYS["binance_key"] or not API_KEYS["binance_secret"]: return
        try:
            timestamp = int(time.time() * 1000)
            headers = {'X-MBX-APIKEY': API_KEYS["binance_key"]}
            saldo_total_usdt = 0.0

            query_spot = f"timestamp={timestamp}"
            sig_spot = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query_spot.encode('utf-8'), hashlib.sha256).hexdigest()
            res_spot = requests.get(f"https://api.binance.com/api/v3/account?{query_spot}&signature={sig_spot}", headers=headers, timeout=5)
            if res_spot.status_code == 200:
                for activo in res_spot.json()["balances"]:
                    if activo["asset"] == "USDT": saldo_total_usdt += float(activo["free"]) + float(activo["locked"])

            query_fund = f"asset=USDT&timestamp={timestamp}"
            sig_fund = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query_fund.encode('utf-8'), hashlib.sha256).hexdigest()
            res_fund = requests.post(f"https://api.binance.com/sapi/v1/asset/get-funding-asset?{query_fund}&signature={sig_fund}", headers=headers, timeout=5)
            if res_fund.status_code == 200:
                for activo in res_fund.json():
                    if activo["asset"] == "USDT": saldo_total_usdt += float(activo["free"]) + float(activo["locked"])

            if res_spot.status_code == 200 or res_fund.status_code == 200:
                for c in CUENTAS:
                    if c["banco"] == "Binance":
                        c["saldo_original"] = saldo_total_usdt
                        break
                guardar_datos()
                if page.route == "/": cambiar_ruta(None)
        except Exception: pass

    def obtener_tasas_red():
        try:
            url_bcv = "https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=bcv"
            resp = requests.get(url_bcv, timeout=10, verify=False).json()
            usd_data = resp.get("monitors", {}).get("usd", {})
            if "price" in usd_data:
                TASAS["BCV"] = float(usd_data["price"])
                fecha_str = usd_data.get("last_update", "")
                ESTADO_APP["fecha_bcv"] = fecha_str if fecha_str else ("Válida para el Lunes" if datetime.now().weekday() in [5, 6] else "Actualizado")
        except Exception: pass

        try:
            url_euro = "https://ve.dolarapi.com/v1/euros/oficial"
            resp_euro = requests.get(url_euro, timeout=10, verify=False)
            if resp_euro.status_code == 200: TASAS["EURO"] = float(resp_euro.json()["promedio"])
        except Exception: pass

        try:
            url_binance = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
            headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            payload = {"fiat": "VES", "page": 1, "rows": 1, "tradeType": "BUY", "asset": "USDT", "countries": [], "payTypes": [], "publisherType": "merchant"}
            resp_compra = requests.post(url_binance, json=payload, headers=headers, timeout=10, verify=False).json()
            if "data" in resp_compra and len(resp_compra["data"]) > 0: TASAS["USDT_COMPRA"] = float(resp_compra["data"][0]["adv"]["price"])
            
            payload["tradeType"] = "SELL"
            resp_venta = requests.post(url_binance, json=payload, headers=headers, timeout=10, verify=False).json()
            if "data" in resp_venta and len(resp_venta["data"]) > 0: TASAS["USDT_VENTA"] = float(resp_venta["data"][0]["adv"]["price"])
        except Exception: pass

    def bucle_sincronizacion():
        while True:
            time.sleep(300) 
            obtener_tasas_red()
            actualizar_saldo_binance()
            if page.route in ["/", "/transaccion", "/calculadora"]:
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


    # ==========================================
    # DIÁLOGOS Y POPUPS
    # ==========================================
    def cerrar_dialogo_detalle(e):
        page.close(dialog_detalle)

    def borrar_movimiento_desde_dialogo(e):
        mov = ESTADO_APP["movimiento_seleccionado"]
        if mov:
            for c in CUENTAS:
                if c["banco"] == mov["banco"]:
                    c["saldo_original"] += mov["monto"] if mov["tipo"] == "gasto" else -mov["monto"]
            MOVIMIENTOS[:] = [m for m in MOVIMIENTOS if m["id"] != mov["id"]]
            guardar_datos()
            
        page.close(dialog_detalle)
        cambiar_ruta(None)
        page.open(ft.SnackBar(ft.Text("Movimiento eliminado", color=ft.colors.WHITE), bgcolor=ft.colors.RED_700))

    ui_det_titulo = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=COLOR_DORADO)
    ui_det_monto = ft.Text("", size=24, weight=ft.FontWeight.BOLD)
    ui_det_fecha = ft.Text("", color=ft.colors.WHITE54)
    ui_det_tasa = ft.Text("", color=ft.colors.WHITE70)
    ui_det_usd = ft.Text("", color=ft.colors.WHITE70, weight=ft.FontWeight.BOLD)

    dialog_detalle = ft.AlertDialog(
        bgcolor="#1A1A1A", title=ft.Text("Detalle de Transacción", color=COLOR_DORADO),
        content=ft.Column([ui_det_titulo, ui_det_monto, ft.Divider(color=ft.colors.WHITE24), ui_det_fecha, ui_det_tasa, ui_det_usd], tight=True),
        actions=[
            ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED_400, tooltip="Eliminar", on_click=borrar_movimiento_desde_dialogo),
            ft.Container(expand=True),
            ft.ElevatedButton("Cerrar", bgcolor=COLOR_DORADO, color=COLOR_NEGRO_PURO, on_click=cerrar_dialogo_detalle)
        ]
    )

    def abrir_detalle_movimiento(mov):
        ESTADO_APP["movimiento_seleccionado"] = mov
        ui_det_titulo.value = mov["titulo"]
        ui_det_monto.value = f"{'+' if mov['tipo']=='ingreso' else '-'} {mov['monto']:,.2f}"
        ui_det_monto.color = ft.colors.GREEN_400 if mov['tipo']=='ingreso' else ft.colors.RED_400
        ui_det_fecha.value = f"Fecha: {mov['fecha']}"
        ui_det_tasa.value = f"Tasa BCV del día: {mov['tasa_historica']:,.2f} Bs"
        ui_det_usd.value = f"Valor Congelado: {mov['eq_usd']:,.2f} USD"
        page.open(dialog_detalle)

    def confirmar_eliminar_banco(e):
        banco = ESTADO_APP["banco_activo"]
        CUENTAS[:] = [c for c in CUENTAS if c["banco"] != banco]
        MOVIMIENTOS[:] = [m for m in MOVIMIENTOS if m["banco"] != banco]
        guardar_datos()
        
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

    dd_nuevo_banco = ft.Dropdown(label="Selecciona un Banco", options=[ft.dropdown.Option(b) for b in BANCOS_DISPONIBLES.keys()], border_color=COLOR_DORADO)
    dd_nueva_moneda = ft.Dropdown(label="Moneda", options=[ft.dropdown.Option("Bs"), ft.dropdown.Option("USD"), ft.dropdown.Option("USDT")], value="Bs", border_color=COLOR_DORADO)
    txt_nuevo_saldo = ft.TextField(label="Saldo Inicial", value="0", border_color=COLOR_DORADO, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)

    def guardar_nuevo_banco(e):
        if not dd_nuevo_banco.value:
            page.open(ft.SnackBar(ft.Text("Selecciona un banco", color=COLOR_NEGRO_PURO), bgcolor="red")); return
        if any(c["banco"] == dd_nuevo_banco.value for c in CUENTAS):
            page.open(ft.SnackBar(ft.Text("Este banco ya está registrado", color=COLOR_NEGRO_PURO), bgcolor="red")); return

        try: saldo = float(txt_nuevo_saldo.value.replace(",", "."))
        except ValueError: saldo = 0.0

        CUENTAS.append({"banco": dd_nuevo_banco.value, "saldo_original": saldo, "moneda": dd_nueva_moneda.value, "logo": BANCOS_DISPONIBLES[dd_nuevo_banco.value]})
        guardar_datos() 
        page.close(dialog_agregar)
        cambiar_ruta(None)
        page.open(ft.SnackBar(ft.Text("Banco agregado con éxito", color=COLOR_NEGRO_PURO), bgcolor=COLOR_DORADO))

    dialog_agregar = ft.AlertDialog(
        bgcolor="#1A1A1A", title=ft.Text("Agregar Nueva Cuenta", color=COLOR_DORADO, weight=ft.FontWeight.BOLD),
        content=ft.Column([dd_nuevo_banco, dd_nueva_moneda, txt_nuevo_saldo], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dialog_agregar)),
            ft.ElevatedButton("Agregar", bgcolor=COLOR_DORADO, color=COLOR_NEGRO_PURO, on_click=guardar_nuevo_banco)
        ]
    )

    # ==========================================
    # CALENDARIO (DATE PICKER)
    # ==========================================
    def cambiar_fecha_inicio(e):
        if dp_inicio.value: ESTADO_APP["fecha_inicio"] = dp_inicio.value.strftime("%d/%m/%Y"); cambiar_ruta(None)
    def cambiar_fecha_fin(e):
        if dp_fin.value: ESTADO_APP["fecha_fin"] = dp_fin.value.strftime("%d/%m/%Y"); cambiar_ruta(None)

    dp_inicio = ft.DatePicker(on_change=cambiar_fecha_inicio)
    dp_fin = ft.DatePicker(on_change=cambiar_fecha_fin)
    page.overlay.extend([dp_inicio, dp_fin])

    # ==========================================
    # GESTOR DE RUTAS E INTERFAZ DINÁMICA
    # ==========================================
    def cambiar_moneda_vista(e, nueva_moneda):
        ESTADO_APP["moneda_vista"] = nueva_moneda
        cambiar_ruta(None) 

    def cambiar_ruta(e):
        es_oscuro = page.theme_mode == ft.ThemeMode.DARK
        BG_COLOR = COLOR_NEGRO_PURO if es_oscuro else "#F8F9FA"
        CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
        TXT_PRINC = ft.colors.WHITE if es_oscuro else COLOR_NEGRO_PURO
        TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
        logo_actual = "mandy_logo.png" if es_oscuro else "zoe_logo.jpg"

        page.views.clear()

        ui_fecha_tiempo = ft.Row([
            ft.IconButton(ft.icons.ARROW_BACK_IOS, icon_color=COLOR_DORADO, icon_size=16, on_click=lambda _: viajar_tiempo("atras")),
            ft.Text(f"BCV: {ESTADO_APP['fecha_bcv']}", color=TXT_PRINC, size=14, weight=ft.FontWeight.BOLD),
            ft.IconButton(ft.icons.ARROW_FORWARD_IOS, icon_color=COLOR_DORADO, icon_size=16, on_click=lambda _: viajar_tiempo("futuro")),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=0)

        # --- RUTA 1: INICIO ---
        if page.route == "/":
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

            # NUEVO BOTÓN DE PAGO MÓVIL
            btn_pago_movil = ft.Container(
                content=ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.icons.MOBILE_FRIENDLY, color=COLOR_NEGRO_PURO), ft.Text("COBRAR PAGO MÓVIL", color=COLOR_NEGRO_PURO, weight=ft.FontWeight.BOLD, size=14)], alignment=ft.MainAxisAlignment.CENTER),
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

            page.views.append(ft.View("/", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
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
                btn_pago_movil, # <--- Botón insertado aquí
                ft.Container(expand=True),
                ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.CALCULATE, color=COLOR_NEGRO_PURO), ft.Text("CALCULADORA", color=COLOR_NEGRO_PURO, weight=ft.FontWeight.BOLD, size=16)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_DORADO, height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=lambda _: page.go("/calculadora"))
            ]))

        # --- RUTA NUEVA: COBRAR PAGO MÓVIL ---
        elif page.route == "/pagomovil":
            b_pm = page.client_storage.get("pm_banco") or ""
            t_pm = page.client_storage.get("pm_telefono") or ""
            c_pm = page.client_storage.get("pm_cedula") or ""

            dd_pm_banco = ft.Dropdown(label="Tu Banco", value=b_pm if b_pm in CODIGOS_PAGO_MOVIL else None, options=[ft.dropdown.Option(b) for b in CODIGOS_PAGO_MOVIL], border_color=COLOR_DORADO, color=TXT_PRINC)
            txt_pm_telefono = ft.TextField(label="Tu Teléfono (Ej: 04141234567)", value=t_pm, border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC, keyboard_type=ft.KeyboardType.PHONE)
            txt_pm_cedula = ft.TextField(label="Tu Cédula (Ej: V12345678)", value=c_pm, border_color=CAJA_COLOR, focused_border_color=COLOR_DORADO, color=TXT_PRINC)
            txt_pm_monto = ft.TextField(label="Monto a Cobrar (Bs)", border_color=COLOR_DORADO, focused_border_color=COLOR_DORADO, color=TXT_PRINC, input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9.,]*$"), keyboard_type=ft.KeyboardType.NUMBER)
            
            ui_equiv_usd = ft.Text("0.00 $", color=COLOR_DORADO, size=18, weight=ft.FontWeight.BOLD)

            def pm_calcular_usd(e):
                if not txt_pm_monto.value:
                    ui_equiv_usd.value = "0.00 $"; page.update(); return
                try:
                    monto = float(txt_pm_monto.value.replace(",", "."))
                    ui_equiv_usd.value = f"{monto/TASAS['BCV']:,.2f} $" if TASAS['BCV'] > 0 else "0.00 $"
                except: pass
                page.update()
            txt_pm_monto.on_change = pm_calcular_usd

            def copiar_pago_movil(e):
                if not dd_pm_banco.value or not txt_pm_telefono.value or not txt_pm_cedula.value or not txt_pm_monto.value:
                    page.open(ft.SnackBar(ft.Text("Completa todos los campos primero.", color=COLOR_NEGRO_PURO), bgcolor="red")); return
                
                page.client_storage.set("pm_banco", dd_pm_banco.value)
                page.client_storage.set("pm_telefono", txt_pm_telefono.value)
                page.client_storage.set("pm_cedula", txt_pm_cedula.value)

                codigo = dd_pm_banco.value.split(" - ")[0]
                monto_float = float(txt_pm_monto.value.replace(",", "."))
                monto_str = f"{monto_float:.2f}".replace(".", ",")

                texto_copiar = f"📱 *DATOS DE PAGO MÓVIL*\nBanco: {dd_pm_banco.value}\nTeléfono: {txt_pm_telefono.value}\nCédula: {txt_pm_cedula.value}\nMonto: {monto_str} Bs\n\n⬇️ *Copia estas 4 líneas para pegado rápido:*\n{codigo}\n{txt_pm_telefono.value}\n{txt_pm_cedula.value}\n{monto_str}"
                
                page.set_clipboard(texto_copiar)
                page.open(ft.SnackBar(ft.Text("¡Copiado! Listo para pegar en WhatsApp o el Banco.", color=COLOR_NEGRO_PURO, weight=ft.FontWeight.BOLD), bgcolor=ft.colors.GREEN_400))

            page.views.append(ft.View("/pagomovil", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
                ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2),
                ft.AppBar(title=ft.Text("Cobrar Pago Móvil", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
                ft.Text("Tus Datos (Se guardan automáticamente)", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
                dd_pm_banco, txt_pm_telefono, txt_pm_cedula,
                ft.Divider(color=TXT_SECUN, height=30),
                ft.Text("¿Cuánto vas a cobrar?", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
                txt_pm_monto,
                ft.Row([ft.Text("Equivalente:", color=TXT_SECUN), ui_equiv_usd], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(expand=True),
                ft.ElevatedButton(content=ft.Row([ft.Icon(ft.icons.COPY, color=COLOR_NEGRO_PURO), ft.Text("COPIAR DATOS", color=COLOR_NEGRO_PURO, weight=ft.FontWeight.BOLD, size=16)], alignment=ft.MainAxisAlignment.CENTER), bgcolor=COLOR_DORADO, height=60, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=copiar_pago_movil)
            ]))

        # --- RUTA 2: CALCULADORA ---
        elif page.route == "/calculadora":
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
            page.views.append(ft.View("/calculadora", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
                ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2, margin=ft.margin.only(bottom=10)),
                ft.AppBar(title=ft.Text("Mercado", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
                ui_fecha_tiempo, ft.Container(height=10),
                ft.Row([
                    ft.Column([ft.Text("BCV", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['BCV']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([ft.Text("EURO", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['EURO']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([ft.Text("P2P COM", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['USDT_COMPRA']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column([ft.Text("P2P VEN", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), ft.Text(f"{TASAS['USDT_VENTA']:.2f}", color=TXT_PRINC, weight=ft.FontWeight.BOLD)], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=TXT_SECUN, height=30), txt_bs, txt_dolar, txt_euro, txt_usdt_c, txt_usdt_v,
                ft.Container(content=ft.Text(f"Diferencia USDT y $ BCV = {b_pct:.2f}% ({b_bs:,.2f} Bs)", color=COLOR_DORADO, size=15, weight=ft.FontWeight.BOLD), alignment=ft.alignment.center, padding=10)
            ]))

        # --- RUTA 3: TRANSACCIÓN ---
        elif page.route == "/transaccion":
            banco = ESTADO_APP["banco_activo"]
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
                    page.open(ft.SnackBar(ft.Text("Llena todos los campos", color=COLOR_NEGRO_PURO), bgcolor="red")); return
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
                    guardar_datos() 
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

            page.views.append(ft.View("/transaccion", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
                ft.Container(height=3, bgcolor=COLOR_TEMA, border_radius=2),
                ft.AppBar(title=ft.Text(banco, color=COLOR_TEMA), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_TEMA, on_click=lambda _: page.go("/"))),
                tabs, ft.Container(height=10), txt_m, dd_cat, ft.Container(height=10), recuadro_tasas, ft.Container(expand=True),
                ft.ElevatedButton("GUARDAR MOVIMIENTO", color=COLOR_NEGRO_PURO if es_oscuro else ft.colors.WHITE, bgcolor=COLOR_TEMA, height=60, width=400, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=30)), on_click=guardar_trans)
            ]))

        # --- RUTA 4: EDITAR SALDO ---
        elif page.route == "/editar":
            banco = ESTADO_APP["banco_activo"]
            saldo_actual = next(c["saldo_original"] for c in CUENTAS if c["banco"] == banco)
            txt_nuevo = ft.TextField(label="Nuevo Saldo Manual", value=str(saldo_actual), color=TXT_PRINC, border_color=COLOR_DORADO, keyboard_type=ft.KeyboardType.NUMBER)
            
            def guardar_edicion(e):
                try:
                    monto = float(txt_nuevo.value.replace(",", "."))
                    for c in CUENTAS:
                        if c["banco"] == banco: c["saldo_original"] = monto; break
                    guardar_datos()
                    page.go("/")
                except: pass

            def guardar_api(e):
                page.client_storage.set("binance_key", txt_api_key_ed.value)
                page.client_storage.set("binance_secret", txt_api_secret_ed.value)
                API_KEYS["binance_key"] = txt_api_key_ed.value
                API_KEYS["binance_secret"] = txt_api_secret_ed.value
                page.open(ft.SnackBar(ft.Text("Sincronizando con Binance...", color=COLOR_NEGRO_PURO), bgcolor=COLOR_DORADO))
                threading.Thread(target=actualizar_saldo_binance, daemon=True).start()
                page.go("/")

            controles_editar = [
                ft.AppBar(title=ft.Text(f"Configurar {banco}", color=COLOR_DORADO), bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
                ft.Text("1. Ajuste Manual de Saldo:", color=TXT_PRINC, weight=ft.FontWeight.BOLD), txt_nuevo,
                ft.ElevatedButton("ACTUALIZAR MANUALMENTE", color=COLOR_NEGRO_PURO, bgcolor=COLOR_DORADO, width=400, on_click=guardar_edicion),
            ]

            if banco == "Binance":
                txt_api_key_ed = ft.TextField(label="API Key (Lectura)", password=True, border_color=COLOR_DORADO, value=API_KEYS["binance_key"])
                txt_api_secret_ed = ft.TextField(label="Secret Key (Lectura)", password=True, border_color=COLOR_DORADO, value=API_KEYS["binance_secret"])
                controles_editar.extend([
                    ft.Divider(color=TXT_SECUN, height=40),
                    ft.Text("2. Sincronización Automática (API):", color=TXT_PRINC, weight=ft.FontWeight.BOLD),
                    ft.Text("Las llaves se guardan encriptadas en este dispositivo.", color=TXT_SECUN, size=11),
                    txt_api_key_ed, txt_api_secret_ed,
                    ft.ElevatedButton("GUARDAR Y SINCRONIZAR API", color=COLOR_NEGRO_PURO, bgcolor=COLOR_DORADO, width=400, on_click=guardar_api)
                ])
            else:
                controles_editar.extend([ft.Container(expand=True), ft.ElevatedButton("ELIMINAR CUENTA", color=ft.colors.WHITE, bgcolor=ft.colors.RED_700, width=400, on_click=lambda _: page.open(dialog_eliminar))])

            page.views.append(ft.View("/editar", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=controles_editar))

        # --- RUTA 5: HISTORIAL ---
        elif page.route == "/historial":
            banco = ESTADO_APP["banco_activo"]
            moneda_base = next(c["moneda"] for c in CUENTAS if c["banco"] == banco)
            logo_banco = next(c["logo"] for c in CUENTAS if c["banco"] == banco)
            
            ui_banco_header = ft.Row([ft.Container(content=ft.Image(src=logo_banco, width=35, height=35, fit=ft.ImageFit.CONTAIN), border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE), ft.Text(banco, color=COLOR_DORADO, size=18, weight=ft.FontWeight.BOLD)], spacing=10)
            fila_fechas = ft.Row([
                ft.ElevatedButton(f"In: {ESTADO_APP['fecha_inicio']}", icon=ft.icons.CALENDAR_TODAY, color=TXT_PRINC, bgcolor=CAJA_COLOR, on_click=lambda _: page.open(dp_inicio)),
                ft.ElevatedButton(f"Fin: {ESTADO_APP['fecha_fin']}", icon=ft.icons.CALENDAR_MONTH, color=TXT_PRINC, bgcolor=CAJA_COLOR, on_click=lambda _: page.open(dp_fin)),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            movs_banco = [m for m in MOVIMIENTOS if m["banco"] == banco]
            total_gastos = sum(m["monto"] for m in movs_banco if m["tipo"] == "gasto")
            cat_totales = {}
            for m in movs_banco:
                if m["tipo"] == "gasto": cat_totales[m["categoria"]] = cat_totales.get(m["categoria"], 0) + m["monto"]

            filas_grafica = []
            colores_morados = [ft.colors.PURPLE_900, ft.colors.PURPLE_700, ft.colors.PURPLE_500, ft.colors.PURPLE_300]
            for i, (cat, monto) in enumerate(sorted(cat_totales.items(), key=lambda x: x[1], reverse=True)):
                pct = (monto / total_gastos * 100) if total_gastos > 0 else 0
                ancho = max(20, int(200 * (pct / 100))) 
                c_morado = colores_morados[i % len(colores_morados)]
                filas_grafica.append(ft.Row([ft.Text(cat[:10], width=80, color=TXT_SECUN, size=12), ft.Container(width=ancho, height=14, bgcolor=c_morado, border_radius=7), ft.Text(f"{pct:.0f}% ({monto:,.0f} {moneda_base})", color=TXT_PRINC, size=12, weight=ft.FontWeight.BOLD)]))
            if not filas_grafica: filas_grafica.append(ft.Text("No hay gastos registrados.", color=TXT_SECUN))
            grafica_ui = ft.Column([ft.Text("Distribución de Gastos", size=16, weight=ft.FontWeight.BOLD, color=TXT_PRINC)] + filas_grafica)

            lista_trans_ui = []
            
            if banco == "Binance":
                lista_trans_ui.append(ft.Container(content=ft.Text("Transacciones P2P Recientes (API Binance):", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), padding=ft.padding.only(top=10, bottom=5)))
                historial_p2p_exitoso = False
                if API_KEYS["binance_key"]:
                    try:
                        timestamp = int(time.time() * 1000)
                        query = f"timestamp={timestamp}"
                        sig = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query.encode('utf-8'), hashlib.sha256).hexdigest()
                        res_p2p = requests.get(f"https://api.binance.com/sapi/v1/c2c/orderMatch/listUserOrderHistory?{query}&signature={sig}", headers={'X-MBX-APIKEY': API_KEYS["binance_key"]}, timeout=5)
                        if res_p2p.status_code == 200:
                            data_p2p = res_p2p.json().get("data", [])
                            if data_p2p:
                                historial_p2p_exitoso = True
                                for trade in data_p2p[:5]: 
                                    tipo_trade = "ingreso" if trade["tradeType"] == "BUY" else "gasto"
                                    fecha_trade = datetime.fromtimestamp(trade["createTime"]/1000).strftime("%d/%m/%Y %I:%M %p")
                                    lista_trans_ui.append(
                                        ft.ListTile(
                                            leading=ft.Icon(ft.icons.SYNC_ALT, color=COLOR_DORADO), 
                                            title=ft.Text(f"{'Compra' if tipo_trade=='ingreso' else 'Venta'} P2P", color=TXT_PRINC, weight=ft.FontWeight.BOLD), 
                                            subtitle=ft.Text(f"{fecha_trade} - Fiat: {trade['totalPrice']} {trade['fiat']}", color=TXT_SECUN, size=11), 
                                            trailing=ft.Text(f"{'+' if tipo_trade=='ingreso' else '-'} {trade['amount']} {trade['asset']}", color=ft.colors.GREEN_400 if tipo_trade == "ingreso" else ft.colors.RED_400, size=16, weight=ft.FontWeight.BOLD)
                                        )
                                    )
                            else:
                                lista_trans_ui.append(ft.Text("No hay operaciones P2P recientes.", color=TXT_SECUN, italic=True))
                    except Exception: pass
                if not historial_p2p_exitoso:
                    lista_trans_ui.append(ft.Container(content=ft.Text("Para ver tu historial automático P2P, asegúrate de que tu API Key tenga permisos de lectura habilitados.", color=TXT_SECUN, size=11, italic=True), padding=10, bgcolor=CAJA_COLOR, border_radius=8))
                lista_trans_ui.append(ft.Divider(color=TXT_SECUN))
                lista_trans_ui.append(ft.Text("Movimientos Manuales Locales:", color=TXT_PRINC, size=14, weight=ft.FontWeight.BOLD))

            for m in movs_banco:
                lista_trans_ui.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(m["icono"], color=ft.colors.GREEN_400 if m["tipo"] == "ingreso" else ft.colors.RED_400), 
                            title=ft.Text(m["titulo"], color=TXT_PRINC, weight=ft.FontWeight.BOLD), 
                            subtitle=ft.Text(f"{m['fecha']} - Tasa: {m.get('tasa_historica', 0):,.2f} Bs | Eq: {m.get('eq_usd', 0):,.2f} $", color=TXT_SECUN, size=11), 
                            trailing=ft.Text(f"{'+' if m['tipo']=='ingreso' else '-'} {m['monto']:,.2f} {moneda_base}", color=ft.colors.GREEN_400 if m["tipo"] == "ingreso" else ft.colors.RED_400, size=16, weight=ft.FontWeight.BOLD),
                        ),
                        on_click=lambda e, mov=m: abrir_detalle_movimiento(mov), ink=True, border_radius=8
                    )
                )

            page.views.append(ft.View("/historial", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
                ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2),
                ft.AppBar(title=ui_banco_header, bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
                fila_fechas, ft.Divider(color=TXT_SECUN, height=30), grafica_ui, ft.Divider(color=TXT_SECUN, height=30),
                ft.Text("Últimos Movimientos", size=14, weight=ft.FontWeight.BOLD, color=TXT_PRINC),
                ft.Column(lista_trans_ui)
            ]))

        page.update()

    def regresar(e):
        page.views.pop()
        page.go(page.views[-1].route)

    page.on_route_change = cambiar_ruta
    page.on_view_pop = regresar
    
    page.views.append(ft.View("/cargando", bgcolor=COLOR_NEGRO_PURO, controls=[
        ft.Container(content=ft.Column([ft.Text("Zoe For Me", size=36, weight=ft.FontWeight.BOLD, italic=True, color=COLOR_DORADO), ft.Container(height=20), ft.Container(content=ft.Image(src="zoe_logo.jpg", width=160, height=160, fit=ft.ImageFit.CONTAIN), border_radius=30, clip_behavior=ft.ClipBehavior.HARD_EDGE), ft.Container(height=40), ft.ProgressRing(color=COLOR_DORADO, stroke_width=3), ft.Container(height=15), ft.Text("Conectando con el mercado...", color=COLOR_DORADO, weight=ft.FontWeight.W_500, size=16)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, expand=True)
    ]))
    page.update()

    obtener_tasas_red()
    actualizar_saldo_binance()
    threading.Thread(target=bucle_sincronizacion, daemon=True).start()
    page.go("/") 

ft.app(target=main, assets_dir="assets")
