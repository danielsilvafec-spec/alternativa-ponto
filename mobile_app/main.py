import flet as ft
import traceback

def main(page: ft.Page):
    try:
        from views.login_view import get_login_view
        
        page.title = "Alternativa Ponto"
        page.padding = 0
        page.theme_mode = ft.ThemeMode.DARK
        
        page.views.clear()
        page.views.append(get_login_view(page))
        page.update()
        
    except Exception as e:
        page.views.clear()
        erro = traceback.format_exc()
        
        # Agora sim: Injetamos uma View verdadeira para que o Flet consiga desenhar o erro
        error_view = ft.View(
            "/error",
            [
                ft.Text("ERRO FATAL ENCONTRADO:", color=ft.Colors.RED_ACCENT, weight="bold", size=20),
                ft.Text(erro, selectable=True, size=11)
            ],
            scroll=ft.ScrollMode.AUTO
        )
        page.views.append(error_view)
        page.update()

ft.run(main)