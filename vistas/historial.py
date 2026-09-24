import flet as ft
from datetime import datetime

# Importamos del cerebro y servicios
from datos import ESTADO_APP, CUENTAS, MOVIMIENTOS, API_KEYS, guardar_datos
from servicios import obtener_historial_p2p

def vista_historial(page: ft.Page, cambiar_ruta, dp_inicio, dp_fin):
    es_oscuro = page.theme_mode == ft.ThemeMode.DARK
    BG_COLOR = "#050505" if es_oscuro else "#F8F9FA"
    CAJA_COLOR = "#1A1A1A" if es_oscuro else "#E9ECEF"
    TXT_PRINC = ft.colors.WHITE if es_oscuro else "#050505"
    TXT_SECUN = ft.colors.WHITE54 if es_oscuro else ft.colors.BLACK87 
    COLOR_DORADO = "#D4AF37"
    
    banco = ESTADO_APP["banco_activo"]
    
    if not banco: return ft.View("/historial", bgcolor=BG_COLOR)
        
    moneda_base = next((c["moneda"] for c in CUENTAS if c["banco"] == banco), "Bs")
    logo_banco = next((c["logo"] for c in CUENTAS if c["banco"] == banco), "")

    # ==========================================
    # DIÁLOGOS Y POPUPS (Internos de la vista)
    # ==========================================
    ui_det_titulo = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=COLOR_DORADO)
    ui_det_monto = ft.Text("", size=24, weight=ft.FontWeight.BOLD)
    ui_det_fecha = ft.Text("", color=ft.colors.WHITE54)
    ui_det_tasa = ft.Text("", color=ft.colors.WHITE70)
    ui_det_usd = ft.Text("", color=ft.colors.WHITE70, weight=ft.FontWeight.BOLD)

    def cerrar_dialogo_detalle(e):
        page.close(dialog_detalle)

    def borrar_movimiento_desde_dialogo(e):
        mov = ESTADO_APP["movimiento_seleccionado"]
        if mov:
            for c in CUENTAS:
                if c["banco"] == mov["banco"]:
                    c["saldo_original"] += mov["monto"] if mov["tipo"] == "gasto" else -mov["monto"]
            MOVIMIENTOS[:] = [m for m in MOVIMIENTOS if m["id"] != mov["id"]]
            guardar_datos(page)
            
        page.close(dialog_detalle)
        cambiar_ruta(None)
        page.open(ft.SnackBar(ft.Text("Movimiento eliminado", color=ft.colors.WHITE), bgcolor=ft.colors.RED_700))

    dialog_detalle = ft.AlertDialog(
        bgcolor="#1A1A1A", title=ft.Text("Detalle de Transacción", color=COLOR_DORADO),
        content=ft.Column([ui_det_titulo, ui_det_monto, ft.Divider(color=ft.colors.WHITE24), ui_det_fecha, ui_det_tasa, ui_det_usd], tight=True),
        actions=[
            ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED_400, tooltip="Eliminar", on_click=borrar_movimiento_desde_dialogo),
            ft.Container(expand=True),
            ft.ElevatedButton("Cerrar", bgcolor=COLOR_DORADO, color="#050505", on_click=cerrar_dialogo_detalle)
        ]
    )

    def abrir_detalle_movimiento(mov):
        ESTADO_APP["movimiento_seleccionado"] = mov
        ui_det_titulo.value = mov["titulo"]
        ui_det_monto.value = f"{'+' if mov['tipo']=='ingreso' else '-'} {mov['monto']:,.2f}"
        ui_det_monto.color = ft.colors.GREEN_400 if mov['tipo']=='ingreso' else ft.colors.RED_400
        ui_det_fecha.value = f"Fecha: {mov['fecha']}"
        ui_det_tasa.value = f"Tasa BCV del día: {mov.get('tasa_historica', 0):,.2f} Bs"
        ui_det_usd.value = f"Valor Congelado: {mov.get('eq_usd', 0):,.2f} USD"
        page.open(dialog_detalle)

    # ==========================================
    # CONSTRUCCIÓN DE LA VISTA
    # ==========================================
    # Ya no hay botón de refrescar aquí.
    ui_banco_header = ft.Row([ft.Container(content=ft.Image(src=logo_banco, width=35, height=35, fit=ft.ImageFit.CONTAIN), border_radius=8, clip_behavior=ft.ClipBehavior.HARD_EDGE), ft.Text(banco, color=COLOR_DORADO, size=18, weight=ft.FontWeight.BOLD)], spacing=10)
    
    def abrir_dp_inicio(e):
        dp_inicio.value = datetime.strptime(ESTADO_APP['fecha_inicio'], "%d/%m/%Y")
        page.open(dp_inicio)
    def abrir_dp_fin(e):
        dp_fin.value = datetime.strptime(ESTADO_APP['fecha_fin'], "%d/%m/%Y")
        page.open(dp_fin)

    fila_fechas = ft.Row([
        ft.ElevatedButton(f"In: {ESTADO_APP['fecha_inicio']}", icon=ft.icons.CALENDAR_TODAY, color=TXT_PRINC, bgcolor=CAJA_COLOR, on_click=abrir_dp_inicio),
        ft.ElevatedButton(f"Fin: {ESTADO_APP['fecha_fin']}", icon=ft.icons.CALENDAR_MONTH, color=TXT_PRINC, bgcolor=CAJA_COLOR, on_click=abrir_dp_fin),
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
        lista_trans_ui.append(ft.Container(content=ft.Text("Transacciones P2P (Últimos 90 días):", color=COLOR_DORADO, size=14, weight=ft.FontWeight.BOLD), padding=ft.padding.only(top=10, bottom=5)))
        
        data_p2p = obtener_historial_p2p()
        if data_p2p:
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
            if API_KEYS.get("binance_key"):
                lista_trans_ui.append(ft.Container(content=ft.Text("Para ver tu historial automático P2P, asegúrate de que tu API Key tenga permisos de lectura habilitados.", color=TXT_SECUN, size=11, italic=True), padding=10, bgcolor=CAJA_COLOR, border_radius=8))
            else:
                lista_trans_ui.append(ft.Text("No hay operaciones P2P recientes.", color=TXT_SECUN, italic=True))
        
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

    return ft.View("/historial", scroll=ft.ScrollMode.AUTO, bgcolor=BG_COLOR, padding=20, controls=[
        ft.Container(height=3, bgcolor=COLOR_DORADO, border_radius=2),
        ft.AppBar(title=ui_banco_header, bgcolor=BG_COLOR, leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color=COLOR_DORADO, on_click=lambda _: page.go("/"))),
        fila_fechas, ft.Divider(color=TXT_SECUN, height=30), grafica_ui, ft.Divider(color=TXT_SECUN, height=30),
        ft.Text("Últimos Movimientos", size=14, weight=ft.FontWeight.BOLD, color=TXT_PRINC),
        ft.Column(lista_trans_ui)
    ])