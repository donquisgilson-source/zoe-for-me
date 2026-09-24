import requests
import time
import hmac
import hashlib
import urllib3
from datetime import datetime
import flet as ft

from datos import TASAS, ESTADO_APP, API_KEYS, CUENTAS, HISTORIAL_TASAS, guardar_datos

urllib3.disable_warnings()

# --- NUEVO: Sincronizador de Relojes para Binance ---
def obtener_tiempo_binance():
    try:
        return requests.get("https://api.binance.com/api/v3/time", timeout=5).json()["serverTime"]
    except:
        return int(time.time() * 1000)
# ----------------------------------------------------

def obtener_tasas_red(page: ft.Page = None):
    try:
        url_usd = "https://ve.dolarapi.com/v1/dolares/oficial"
        resp_usd = requests.get(url_usd, timeout=10, verify=False)
        if resp_usd.status_code == 200: 
            data = resp_usd.json()
            TASAS["BCV"] = float(data["promedio"])
            
            fecha_api = data.get("fechaActualizacion", "")
            if fecha_api:
                fecha_corta = fecha_api.split("T")[0]
                fecha_obj = datetime.strptime(fecha_corta, "%Y-%m-%d")
                ESTADO_APP["fecha_bcv"] = fecha_obj.strftime("%d/%m/%Y")
            else:
                ESTADO_APP["fecha_bcv"] = datetime.now().strftime("%d/%m/%Y")
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

    fecha_str = ESTADO_APP["fecha_bcv"]
    HISTORIAL_TASAS[fecha_str] = {
        "BCV": TASAS["BCV"],
        "EURO": TASAS["EURO"],
        "USDT_COMPRA": TASAS["USDT_COMPRA"],
        "USDT_VENTA": TASAS["USDT_VENTA"]
    }
    if page: guardar_datos(page)


def actualizar_saldo_binance(page: ft.Page):
    if not API_KEYS.get("binance_key") or not API_KEYS.get("binance_secret"): 
        return False, "Faltan credenciales API"
    try:
        timestamp = obtener_tiempo_binance() # Sincronizamos hora
        headers = {'X-MBX-APIKEY': API_KEYS["binance_key"]}
        saldo_total_usdt = 0.0

        query_spot = f"timestamp={timestamp}"
        sig_spot = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query_spot.encode('utf-8'), hashlib.sha256).hexdigest()
        res_spot = requests.get(f"https://api.binance.com/api/v3/account?{query_spot}&signature={sig_spot}", headers=headers, timeout=5)
        
        if res_spot.status_code != 200:
            print("ERROR BINANCE (SPOT):", res_spot.text)
            return False, f"Bloqueo Binance: {res_spot.json().get('msg', 'Revisa tus llaves API')}"

        for activo in res_spot.json()["balances"]:
            if activo["asset"] == "USDT": saldo_total_usdt += float(activo["free"]) + float(activo["locked"])

        query_fund = f"asset=USDT&timestamp={timestamp}"
        sig_fund = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query_fund.encode('utf-8'), hashlib.sha256).hexdigest()
        res_fund = requests.post(f"https://api.binance.com/sapi/v1/asset/get-funding-asset?{query_fund}&signature={sig_fund}", headers=headers, timeout=5)
        if res_fund.status_code == 200:
            for activo in res_fund.json():
                if activo["asset"] == "USDT": saldo_total_usdt += float(activo["free"]) + float(activo["locked"])
        else:
            print("ERROR BINANCE (FONDOS):", res_fund.text)

        for c in CUENTAS:
            if c["banco"] == "Binance":
                c["saldo_original"] = saldo_total_usdt
                break
        guardar_datos(page)
        return True, "Sincronizado"
    except Exception as e:
        print("ERROR DE RED BINANCE:", e)
        return False, "Error de red con Binance"

def obtener_historial_p2p():
    if not API_KEYS.get("binance_key") or not API_KEYS.get("binance_secret"):
        return []
    try:
        end_ts = obtener_tiempo_binance() # Sincronizamos hora
        start_ts = end_ts - (90 * 24 * 60 * 60 * 1000)
        query = f"startTimestamp={start_ts}&endTimestamp={end_ts}&rows=10&timestamp={end_ts}"
        
        sig = hmac.new(API_KEYS["binance_secret"].encode('utf-8'), query.encode('utf-8'), hashlib.sha256).hexdigest()
        res_p2p = requests.get(f"https://api.binance.com/sapi/v1/c2c/orderMatch/listUserOrderHistory?{query}&signature={sig}", headers={'X-MBX-APIKEY': API_KEYS["binance_key"]}, timeout=5)
        
        if res_p2p.status_code == 200:
            return res_p2p.json().get("data", [])
        else:
            print("ERROR BINANCE (HISTORIAL):", res_p2p.text)
    except Exception as e: pass
    return []