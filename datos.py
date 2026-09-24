import flet as ft
from datetime import datetime

TASAS = {
    "BCV": 849.56,
    "EURO": 974.00,
    "USDT_COMPRA": 950.00,
    "USDT_VENTA": 940.00
}

ESTADO_APP = {
    "moneda_vista": "Original",
    "fecha_bcv": datetime.now().strftime("%d/%m/%Y"), 
    "trans_tipo": "ingreso",  
    "banco_activo": "",
    "fecha_inicio": datetime.now().replace(day=1).strftime("%d/%m/%Y"), 
    "fecha_fin": datetime.now().strftime("%d/%m/%Y"), 
    "movimiento_seleccionado": None,
    "autenticado": False  # <--- NUEVO: Candado de seguridad
}

API_KEYS = {}
CUENTAS = []
MOVIMIENTOS = []
HISTORIAL_TASAS = {}

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

def inicializar_datos(page: ft.Page):
    global API_KEYS, CUENTAS, MOVIMIENTOS, HISTORIAL_TASAS
    
    API_KEYS.clear()
    API_KEYS["binance_key"] = page.client_storage.get("binance_key") or ""
    API_KEYS["binance_secret"] = page.client_storage.get("binance_secret") or ""

    CUENTAS.clear()
    cuentas_guardadas = page.client_storage.get("zoe_cuentas")
    if cuentas_guardadas: 
        CUENTAS.extend(cuentas_guardadas)
    else:
        CUENTAS.extend([
            {"banco": "Banco Mercantil", "saldo_original": 0.0, "moneda": "Bs", "logo": "mercantil.png"},
            {"banco": "Banco de Venezuela", "saldo_original": 0.0, "moneda": "Bs", "logo": "bancodevenezuela.png"},
            {"banco": "Binance", "saldo_original": 0.0, "moneda": "USDT", "logo": "binance.png"},
            {"banco": "Divisas Físicas", "saldo_original": 0.0, "moneda": "USD", "logo": "divisas.png"}
        ])

    MOVIMIENTOS.clear()
    movs_guardados = page.client_storage.get("zoe_movimientos")
    if movs_guardados: MOVIMIENTOS.extend(movs_guardados)

    HISTORIAL_TASAS.clear()
    hist_tasas = page.client_storage.get("zoe_historial_tasas")
    if hist_tasas: HISTORIAL_TASAS.update(hist_tasas)

def guardar_datos(page: ft.Page):
    page.client_storage.set("zoe_cuentas", CUENTAS)
    page.client_storage.set("zoe_movimientos", MOVIMIENTOS)
    page.client_storage.set("zoe_historial_tasas", HISTORIAL_TASAS)