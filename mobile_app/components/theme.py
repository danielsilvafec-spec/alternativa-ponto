# mobile_app/components/theme.py
import flet as ft

COR_TEXTO_CLARO = "#ffffff"
COR_LARANJA = "#d35400"
COR_VERMELHO_ESCURO = "#710000"

# O Flet atualizado usa coordenadas para alinhamento:
# ft.Alignment(-1.0, -1.0) = Top Left
# ft.Alignment(1.0, 1.0) = Bottom Right

GRADIENTE_FUNDO = ft.LinearGradient(
    begin=ft.Alignment(-1.0, -1.0),
    end=ft.Alignment(1.0, 1.0),
    colors=["#710000", "#1a0000"]
)

GRADIENTE_BOTAO_ACAO = ft.LinearGradient(
    begin=ft.Alignment(-1.0, -1.0),
    end=ft.Alignment(1.0, 1.0),
    colors=["#a99590", "#710000"]
)

SOMBRA_MODERNA = ft.BoxShadow(
    spread_radius=1,
    blur_radius=10,
    color="#4D000000",
    offset=ft.Offset(0, 4)
)