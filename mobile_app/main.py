import flet as ft
import traceback

def main(page: ft.Page):
    try:
        page.title = "Teste de Isolamento"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        page.add(
            ft.Text("O motor do Flet está a funcionar!", size=20, color=ft.Colors.GREEN_400),
            ft.Text("Se consegue ler isto, o problema está nos ficheiros importados (login_view ou api_client).", text_align=ft.TextAlign.CENTER)
        )
    except Exception as e:
        erro = traceback.format_exc()
        page.add(ft.Text(erro, color=ft.Colors.RED, selectable=True))

ft.run(main)