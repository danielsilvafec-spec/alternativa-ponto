import flet as ft
import traceback

def main(page: ft.Page):
    try:
        # Tentamos importar a sua view verdadeira AQUI DENTRO
        from views.login_view import get_login_view
        
        page.title = "Alternativa Ponto"
        page.padding = 0
        page.theme_mode = ft.ThemeMode.DARK
        
        page.views.clear()
        page.views.append(get_login_view(page))
        page.update()
        
    except Exception as e:
        # Se o login_view ou o api_client tiverem algum erro, vai aparecer no ecrã!
        page.views.clear()
        erro = traceback.format_exc()
        page.add(
            ft.Text("ERRO FATAL ENCONTRADO:", color=ft.Colors.RED_ACCENT, weight="bold", size=20),
            ft.Text(erro, selectable=True, size=11)
        )

ft.run(main)