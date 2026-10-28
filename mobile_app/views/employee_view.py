# mobile_app/views/employee_view.py
import flet as ft
import datetime
import requests
import threading
import time
from components.theme import GRADIENTE_FUNDO, GRADIENTE_BOTAO_ACAO, SOMBRA_MODERNA, COR_TEXTO_CLARO, COR_LARANJA
from api_client import ApiClient

def get_employee_view(page: ft.Page):
    
    # Variáveis de Estado
    current_lat = 0.0
    current_lng = 0.0

    # Componentes Visuais
    lbl_relogio = ft.Text("00:00:00", size=48, weight="bold", color=COR_TEXTO_CLARO)
    lbl_data = ft.Text("", size=16, color="#a99590")
    lbl_localizacao = ft.Text("Buscando GPS...", size=12, color=ft.colors.GREEN_300)
    lbl_status = ft.Text("", size=16, weight="bold")
    
    lista_historico = ft.ListView(expand=True, spacing=10, padding=10)

    # Função que atualiza o relógio a cada segundo
    def atualizar_relogio():
        while True:
            agora = datetime.datetime.now()
            lbl_relogio.value = agora.strftime("%H:%M:%S")
            lbl_data.value = agora.strftime("%d/%m/%Y")
            try:
                page.update()
            except:
                break # Se a página fechar, para o loop
            time.sleep(1)

    # Simulação de Geolocalização (Busca baseada na rede atual)
    def buscar_localizacao():
        nonlocal current_lat, current_lng
        try:
            res = requests.get("http://ip-api.com/json/").json()
            current_lat = res.get("lat", 0.0)
            current_lng = res.get("lon", 0.0)
            cidade = res.get("city", "Desconhecida")
            lbl_localizacao.value = f"📍 {cidade} (Lat: {current_lat}, Lng: {current_lng})"
            page.update()
        except:
            lbl_localizacao.value = "📍 Localização Indisponível (Offline)"
            page.update()

    def carregar_historico():
        lista_historico.controls.clear()
        registros = ApiClient.obter_historico_hoje()
        if not registros:
            lista_historico.controls.append(ft.Text("Nenhuma marcação hoje.", color=COR_TEXTO_CLARO))
        else:
            for reg in registros:
                hora = datetime.datetime.fromisoformat(reg['data_hora']).strftime("%H:%M:%S")
                
                # Adiciona a tag visual se for um ajuste manual
                texto_exibicao = f"{reg['tipo']} - {hora}"
                if reg.get('is_ajuste'):
                    texto_exibicao += " (Horário Ajustado)"
                    
                lista_historico.controls.append(
                    ft.Container(
                        content=ft.Text(texto_exibicao, color="#333333", weight="bold"),
                        bgcolor=COR_TEXTO_CLARO,
                        padding=10,
                        border_radius=8
                    )
                )
        page.update()

    def registrar_ponto(e):
        tipo = e.control.data
        sucesso, msg = ApiClient.bater_ponto(tipo, current_lat, current_lng)
        lbl_status.value = msg
        lbl_status.color = ft.colors.GREEN_300 if sucesso else ft.colors.RED_300
        page.update()
        if sucesso:
            carregar_historico()

    drop_tipo_ponto = ft.Dropdown(
        label="Selecione a ação",
        options=[
            ft.dropdown.Option("Entrada"),
            ft.dropdown.Option("Saída para Intervalo"),
            ft.dropdown.Option("Retorno do Intervalo"),
            ft.dropdown.Option("Saída Final")
        ],
        width=300
    )

    def registrar_ponto_dropdown(e):
        if not drop_tipo_ponto.value:
            lbl_status.value = "Selecione uma opção primeiro!"
            lbl_status.color = ft.colors.RED_300
            page.update()
            return
            
        sucesso, msg = ApiClient.bater_ponto(drop_tipo_ponto.value, current_lat, current_lng)
        lbl_status.value = msg
        lbl_status.color = ft.colors.GREEN_300 if sucesso else ft.colors.RED_300
        page.update()
        if sucesso:
            carregar_historico()

    botoes_grid = ft.Column([
        drop_tipo_ponto, 
        ft.ElevatedButton("Confirmar Ponto", bgcolor=COR_LARANJA, color=COR_TEXTO_CLARO, height=50, width=300, on_click=registrar_ponto_dropdown)
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    threading.Thread(target=atualizar_relogio, daemon=True).start()
    threading.Thread(target=buscar_localizacao, daemon=True).start()
    threading.Thread(target=carregar_historico, daemon=True).start()

    # ---- MODAL DE SOLICITAÇÃO DE AJUSTE ----
    txt_data_ajuste = ft.TextField(label="Data (AAAA-MM-DD)", value=datetime.date.today().isoformat())
    txt_hora_ajuste = ft.TextField(label="Hora Correta (HH:MM)")
    drop_tipo_ajuste = ft.Dropdown(label="Tipo", options=[ft.dropdown.Option("Entrada"), ft.dropdown.Option("Saída para Intervalo"), ft.dropdown.Option("Retorno do Intervalo"), ft.dropdown.Option("Saída Final")])
    txt_motivo = ft.TextField(label="Motivo da correção")

    def enviar_ajuste(e):
        if not all([txt_hora_ajuste.value, drop_tipo_ajuste.value, txt_motivo.value]): return
        dados = {"data": txt_data_ajuste.value, "hora_correta": txt_hora_ajuste.value, "tipo": drop_tipo_ajuste.value, "motivo": txt_motivo.value}
        if ApiClient.solicitar_ajuste(dados):
            dialog_ajuste.open = False
            txt_hora_ajuste.value = txt_motivo.value = ""
            page.snack_bar = ft.SnackBar(ft.Text("Ajuste solicitado com sucesso!", color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600)
            page.snack_bar.open = True
            page.update()

    dialog_ajuste = ft.AlertDialog(
        modal=True, title=ft.Text("Solicitar Ajuste de Ponto", weight="bold"),
        content=ft.Column([txt_data_ajuste, txt_hora_ajuste, drop_tipo_ajuste, txt_motivo], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_ajuste, 'open', False) or page.update()), 
            ft.ElevatedButton("Enviar Pedido", bgcolor=COR_LARANJA, color=COR_TEXTO_CLARO, on_click=enviar_ajuste)
        ]
    )

    def abrir_ajuste(e):
        page.dialog = dialog_ajuste
        dialog_ajuste.open = True
        page.update()

    return ft.View(
        "/employee",
        [
            ft.Container(
                content=ft.Column([
                    
                    ft.Row([
                        ft.Image(src="logo.png", width=120, height=40, fit=ft.ImageFit.CONTAIN),
                        ft.Row([
                            ft.ElevatedButton("Painel Admin", on_click=lambda e: page.go("/admin"), visible=(ApiClient.user_data.get("perfil") == "admin")),
                            ft.IconButton(ft.icons.LOGOUT, icon_color=COR_LARANJA, on_click=lambda e: page.go("/login"))
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(height=20),
                    
                    ft.Column([lbl_relogio, lbl_data, ft.Container(height=5), lbl_localizacao], 
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    ft.Container(height=30),
                    lbl_status,
                    botoes_grid,
                    
                    ft.Container(height=20),
                    ft.Text("Histórico de Hoje", size=18, weight="bold", color=COR_LARANJA),
                    ft.Divider(color="#a99590"),
                    lista_historico,
                    
                    ft.ElevatedButton("Solicitar Ajuste Manual", icon=ft.icons.EDIT_CALENDAR, bgcolor="#333333", color=COR_TEXTO_CLARO, on_click=abrir_ajuste)
                ]),
                gradient=GRADIENTE_FUNDO,
                expand=True,
                padding=20
            )
        ],
        padding=0
    )