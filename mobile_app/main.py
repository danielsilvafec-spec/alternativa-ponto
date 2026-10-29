# mobile_app/main.py
import flet as ft
from views.login_view import get_login_view
from views.employee_view import get_employee_view
from views.admin_view import get_admin_view  # <-- Nova importação

def main(page: ft.Page):
    page.title = "Alternativa Ponto"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    def route_change(route):
        page.views.clear()
        
        if page.route == "/login" or page.route == "/":
            page.window_width = 400
            page.window_height = 800
            page.views.append(get_login_view(page))
        elif page.route == "/employee":
            page.window_width = 400
            page.window_height = 800
            page.views.append(get_employee_view(page))
        elif page.route == "/admin":
            # Agora redireciona corretamente para a tela de Admin (que amplia a janela)
            page.views.append(get_admin_view(page))
            
        page.update()

    page.on_route_change = route_change
    page.go("/login")

if __name__ == "__main__":
    ft.app(target=main)
if __name__ == "__main__":
    try:
        ft.app(target=main)
    except AttributeError:
        pass  # No Android/iOS o Flet inicia o main() nativamente, então ignoramos o erro