import flet as ft
from views.login_view import get_login_view
from views.employee_view import get_employee_view
from views.admin_view import get_admin_view

def main(page: ft.Page):
    page.title = "Alternativa Ponto"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK

    def route_change(e):
        page.views.clear()
        
        if page.route == "/login" or page.route == "/":
            page.views.append(get_login_view(page))
        elif page.route == "/employee":
            page.views.append(get_employee_view(page))
        elif page.route == "/admin":
            page.views.append(get_admin_view(page))
            
        page.update()

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    page.go("/login")

# Define assets_dir para garantir o carregamento do icon.png
ft.run(main, assets_dir="assets")