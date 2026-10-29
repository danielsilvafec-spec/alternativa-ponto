import flet as ft
from components.theme import GRADIENTE_FUNDO, GRADIENTE_BOTAO_ACAO, SOMBRA_MODERNA, COR_TEXTO_CLARO
from api_client import ApiClient

def get_login_view(page: ft.Page):
    
    txt_username = ft.TextField(
        label="Usuário", 
        bgcolor="#ffffff", 
        color="#333333", 
        border_radius=10,
        prefix_icon="person"
    )
    
    txt_password = ft.TextField(
        label="Senha", 
        password=True, 
        can_reveal_password=True, 
        bgcolor="#ffffff", 
        color="#333333", 
        border_radius=10,
        prefix_icon="lock"
    )
    
    lbl_error = ft.Text("", color=ft.Colors.RED_200, size=14)

    def on_login_click(e):
        btn_login.disabled = True
        lbl_error.value = "Conectando ao servidor..."
        page.update()

        sucesso, msg = ApiClient.login(txt_username.value, txt_password.value)
        
        btn_login.disabled = False
        if sucesso:
            lbl_error.value = ""
            if ApiClient.user_data["perfil"] == "admin":
                page.go("/admin")
            else:
                page.go("/employee")
        else:
            lbl_error.value = msg
        page.update()

    btn_login = ft.Container(
        content=ft.Text("ENTRAR", color=COR_TEXTO_CLARO, weight="bold", size=16),
        alignment=ft.Alignment(0, 0),
        height=50,
        border_radius=25,
        gradient=GRADIENTE_BOTAO_ACAO,
        shadow=SOMBRA_MODERNA,
        on_click=on_login_click
    )

    form_container = ft.Container(
        content=ft.Column(
            [
                ft.Image(src="icon.png", width=250, height=100, fit="contain"),
                ft.Container(height=30),
                txt_username,
                ft.Container(height=10),
                txt_password,
                ft.Container(height=5),
                lbl_error,
                ft.Container(height=20),
                btn_login
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=40,
        alignment=ft.Alignment(0, 0),
        expand=True
    )

    return ft.View(
        "/login",
        [
            ft.Container(
                content=form_container,
                gradient=GRADIENTE_FUNDO,
                expand=True
            )
        ],
        padding=0
    )