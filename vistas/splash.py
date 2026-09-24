import flet as ft

def vista_splash(page: ft.Page):
    # Toma la imagen inicio_zoe.jpg y la expande a toda la pantalla
    return ft.View(
        "/splash",
        padding=0,
        controls=[
            ft.Container(
                image_src="inicio_zoe.jpg",
                image_fit=ft.ImageFit.COVER,
                expand=True
            )
        ]
    )