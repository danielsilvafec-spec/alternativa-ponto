import flet as ft
from views.login_view import get_login_view

def main(page: ft.Page):
    page.title = "Alternativa Ponto"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    
    # Limpa qualquer ecrã em branco e injeta o login diretamente
    page.views.clear()
    page.views.append(get_login_view(page))
    page.update()

ft.run(main)