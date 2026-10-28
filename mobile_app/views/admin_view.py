# mobile_app/views/admin_view.py
import flet as ft
import datetime
import threading
from components.theme import GRADIENTE_FUNDO, GRADIENTE_BOTAO_ACAO, SOMBRA_MODERNA, COR_TEXTO_CLARO, COR_LARANJA, COR_VERMELHO_ESCURO
from api_client import ApiClient

def get_admin_view(page: ft.Page):
    page.window_width = 1000
    page.window_height = 700
    page.update()

    lista_registros = ft.ListView(expand=True, spacing=10, padding=10)
    lbl_total_usuarios = ft.Text("0", size=24, weight="bold", color=COR_VERMELHO_ESCURO)
    lbl_total_registros = ft.Text("0", size=24, weight="bold", color=COR_VERMELHO_ESCURO)
    
    data_selecionada = None
    lbl_data_filtro = ft.Text("Exibindo: Todos (Últimos 50)", color="#a99590", size=14)

    def carregar_dados():
        usuarios = ApiClient.obter_usuarios_admin()
        registros = ApiClient.obter_registros_admin(data_selecionada)
        
        lbl_total_usuarios.value = str(len(usuarios))
        lbl_total_registros.value = str(len(registros))
        
        lista_registros.controls.clear()
        if not registros:
            lista_registros.controls.append(ft.Text("Nenhum registro encontrado para esta data.", color="#333333"))
        else:
            for reg in registros:
                data_formatada = datetime.datetime.fromisoformat(reg['data_hora']).strftime("%d/%m/%Y %H:%M:%S")
                lat_lng = f"Lat: {reg['lat']}, Lng: {reg['lng']}" if reg['lat'] else "Sem GPS"
                
                tipo_texto = reg['tipo']
                if reg.get('is_ajuste'):
                    tipo_texto += " (Horário Ajustado)"
                
                lista_registros.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(f"{reg['funcionario']} - {tipo_texto}", weight="bold", color=COR_VERMELHO_ESCURO, size=16),
                            ft.Text(f"Data/Hora: {data_formatada}", color="#555555"),
                            ft.Text(f"📍 {lat_lng}", color=ft.colors.BLUE_700, size=12)
                        ]),
                        bgcolor=COR_TEXTO_CLARO, padding=15, border_radius=10, shadow=SOMBRA_MODERNA
                    )
                )
        page.update()

    def on_date_selected(e):
        nonlocal data_selecionada
        if date_picker.value:
            data_selecionada = date_picker.value.strftime("%Y-%m-%d")
            lbl_data_filtro.value = f"Exibindo: {date_picker.value.strftime('%d/%m/%Y')}"
            carregar_dados()

    date_picker = ft.DatePicker(
        on_change=on_date_selected,
        first_date=datetime.datetime(2023, 1, 1),
        last_date=datetime.datetime(2030, 12, 31)
    )
    page.overlay.append(date_picker)

    def limpar_filtro(e):
        nonlocal data_selecionada
        data_selecionada = None
        lbl_data_filtro.value = "Exibindo: Todos (Últimos 50)"
        carregar_dados()

    # ---- MODAL BANCO DE HORAS DO FUNCIONÁRIO ----
    lbl_nome_banco = ft.Text("", weight="bold", color=COR_TEXTO_CLARO, size=16)
    lbl_saldo_banco = ft.Text("", weight="bold", size=20)

    dialog_banco_horas = ft.AlertDialog(
        modal=True,
        title=ft.Text("Banco de Horas Individual", color=COR_TEXTO_CLARO, weight="bold"),
        content=ft.Container(
            content=ft.Column([
                lbl_nome_banco,
                ft.Container(height=10),
                ft.Row([
                    ft.Text("Saldo Acumulado:", color="#cccccc", size=14),
                    lbl_saldo_banco
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], tight=True),
            width=350, padding=10
        ),
        actions=[
            ft.TextButton(
                "Voltar",
                style=ft.ButtonStyle(color=COR_LARANJA),
                on_click=lambda e: (setattr(dialog_banco_horas, 'open', False), setattr(page, 'dialog', dialog_funcionarios), setattr(dialog_funcionarios, 'open', True), page.update())
            )
        ]
    )

    def abrir_modal_banco_horas_usuario(uid, nome):
        dialog_funcionarios.open = False
        lbl_nome_banco.value = f"Funcionário: {nome}"
        lbl_saldo_banco.value = "A carregar..."
        lbl_saldo_banco.color = "#aaaaaa"
        page.dialog = dialog_banco_horas
        dialog_banco_horas.open = True
        page.update()

        saldos = ApiClient.obter_banco_de_horas()
        saldo_info = next((s for s in saldos if s['nome'] == nome), None)
        if saldo_info:
            lbl_saldo_banco.value = saldo_info['saldo']
            lbl_saldo_banco.color = ft.colors.GREEN_400 if saldo_info['positivo'] else ft.colors.RED_400
        else:
            lbl_saldo_banco.value = "0h 00m"
            lbl_saldo_banco.color = COR_TEXTO_CLARO
        page.update()
        
    # ---- MODAL CADASTRAR NOVO FUNCIONÁRIO COM JORNADA ----
    txt_nome = ft.TextField(label="Nome Completo", width=320)
    txt_user = ft.TextField(label="Nome de Usuário", width=320)
    txt_senha = ft.TextField(label="Senha Inicial", password=True, can_reveal_password=True, width=320)
    txt_dep = ft.TextField(label="Departamento", width=320)
    drop_perfil = ft.Dropdown(
        options=[ft.dropdown.Option("funcionario", "Funcionário"), ft.dropdown.Option("admin", "Administrador")],
        value="funcionario",
        width=320
    )
    
    txt_horas = ft.TextField(label="Horas Diárias", value="8.0", width=155)
    txt_intervalo = ft.TextField(label="Intervalo (min)", value="60", width=155)
    txt_entrada = ft.TextField(label="Entrada Padrão", value="08:00", width=155)
    txt_saida = ft.TextField(label="Saída Padrão", value="18:00", width=155)
    
    lbl_feedback = ft.Text("", color=ft.colors.RED_400, size=14)

    def salvar_novo_usuario(e):
        if not all([txt_nome.value, txt_user.value, txt_senha.value, txt_dep.value, txt_horas.value, txt_entrada.value, txt_saida.value, txt_intervalo.value]):
            lbl_feedback.value = "Preencha todos os campos!"
            page.update()
            return
            
        dados = {
            "nome_completo": txt_nome.value.strip(),
            "username": txt_user.value.strip(),
            "senha": txt_senha.value.strip(),
            "departamento": txt_dep.value.strip(),
            "perfil": drop_perfil.value,
            "horas_diarias": float(txt_horas.value),
            "entrada_padrao": txt_entrada.value.strip(),
            "saida_padrao": txt_saida.value.strip(),
            "minutos_intervalo": int(txt_intervalo.value)
        }
        
        sucesso, msg = ApiClient.criar_usuario(dados)
        if sucesso:
            txt_nome.value = txt_user.value = txt_senha.value = txt_dep.value = ""
            txt_horas.value = "8.0"
            txt_entrada.value = "08:00"
            txt_saida.value = "18:00"
            txt_intervalo.value = "60"
            dialog_novo_user.open = False
            page.snack_bar = ft.SnackBar(ft.Text(msg, color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600)
            page.snack_bar.open = True
            page.dialog = dialog_funcionarios
            dialog_funcionarios.open = True
            carregar_dados_funcionarios()
            carregar_dados()
        else:
            lbl_feedback.value = msg
            page.update()

    dialog_novo_user = ft.AlertDialog(
        modal=True,
        title=ft.Text("Cadastrar Novo Funcionário", color=COR_TEXTO_CLARO, weight="bold"),
        content=ft.Container(
            content=ft.Column([
                txt_nome,
                txt_user,
                txt_senha,
                txt_dep,
                drop_perfil,
                ft.Divider(color="#555555"),
                ft.Text("Definição de Jornada", weight="bold", color="#333333", size=14),
                ft.Row([txt_horas, txt_intervalo], width=320),
                ft.Row([txt_entrada, txt_saida], width=320),
                lbl_feedback
            ], tight=True, spacing=8, scroll=ft.ScrollMode.AUTO),
            width=350,
            height=460
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog_novo_user, 'open', False), setattr(page, 'dialog', dialog_funcionarios), setattr(dialog_funcionarios, 'open', True), page.update())),
            ft.ElevatedButton("Salvar", bgcolor=COR_LARANJA, color=COR_TEXTO_CLARO, on_click=salvar_novo_usuario)
        ]
    )

    def abrir_modal_novo_user(e):
        dialog_funcionarios.open = False
        page.dialog = dialog_novo_user
        dialog_novo_user.open = True
        page.update()

    # ---- MODAL DE REDEFINIÇÃO DE SENHA ----
    usuario_selecionado_senha = None
    txt_nova_senha = ft.TextField(label="Nova Senha", password=True, can_reveal_password=True, width=300)

    def salvar_nova_senha(e):
        if not txt_nova_senha.value: return
        sucesso, msg = ApiClient.alterar_senha_usuario(usuario_selecionado_senha, txt_nova_senha.value)
        page.snack_bar = ft.SnackBar(ft.Text(msg, color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600 if sucesso else ft.colors.RED_600)
        page.snack_bar.open = True
        dialog_alterar_senha.open = False
        txt_nova_senha.value = ""
        page.dialog = dialog_funcionarios
        dialog_funcionarios.open = True
        page.update()

    dialog_alterar_senha = ft.AlertDialog(
        modal=True, title=ft.Text("Redefinir Senha", color=COR_TEXTO_CLARO, weight="bold"), content=txt_nova_senha,
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog_alterar_senha, 'open', False), setattr(page, 'dialog', dialog_funcionarios), setattr(dialog_funcionarios, 'open', True), page.update())),
            ft.ElevatedButton("Salvar", bgcolor=COR_LARANJA, color=COR_TEXTO_CLARO, on_click=salvar_nova_senha)
        ]
    )

    # ---- MODAL RELATÓRIO PDF POR FUNCIONÁRIO ----
    usuario_selecionado_pdf = None
    lbl_nome_pdf = ft.Text("", color="#333333", weight="bold")
    txt_mes = ft.TextField(label="Mês (AAAA-MM)", value=datetime.date.today().strftime("%Y-%m"), width=300)
    
    def baixar_pdf_individual(e):
        if usuario_selecionado_pdf and txt_mes.value:
            sucesso, msg = ApiClient.baixar_relatorio_pdf(usuario_selecionado_pdf, txt_mes.value)
            dialog_relatorio.open = False
            page.snack_bar = ft.SnackBar(ft.Text(msg, color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600 if sucesso else ft.colors.RED_600)
            page.snack_bar.open = True
            page.dialog = dialog_funcionarios
            dialog_funcionarios.open = True
            page.update()

    dialog_relatorio = ft.AlertDialog(
        modal=True,
        title=ft.Text("Gerar Relatório PDF", color=COR_TEXTO_CLARO, weight="bold"),
        content=ft.Column([lbl_nome_pdf, txt_mes], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog_relatorio, 'open', False), setattr(page, 'dialog', dialog_funcionarios), setattr(dialog_funcionarios, 'open', True), page.update())),
            ft.ElevatedButton("Baixar PDF", bgcolor=COR_LARANJA, color=COR_TEXTO_CLARO, on_click=baixar_pdf_individual)
        ]
    )

    # ---- MODAL GESTÃO DE FUNCIONÁRIOS ----
    lista_funcionarios = ft.ListView(height=430, spacing=10)

    def carregar_dados_funcionarios():
        lista_funcionarios.controls.clear()
        usuarios = ApiClient.obter_usuarios_admin()
        for u in usuarios:
            def abrir_senha(uid):
                def on_click(e):
                    nonlocal usuario_selecionado_senha
                    usuario_selecionado_senha = uid
                    dialog_funcionarios.open = False
                    page.dialog = dialog_alterar_senha
                    dialog_alterar_senha.open = True
                    page.update()
                return on_click

            def abrir_pdf(uid, nome):
                def on_click(e):
                    nonlocal usuario_selecionado_pdf
                    usuario_selecionado_pdf = uid
                    lbl_nome_pdf.value = f"Funcionário: {nome}"
                    dialog_funcionarios.open = False
                    page.dialog = dialog_relatorio
                    dialog_relatorio.open = True
                    page.update()
                return on_click

            def abrir_banco(uid, nome):
                def on_click(e):
                    abrir_modal_banco_horas_usuario(uid, nome)
                return on_click

            def excluir_func(uid):
                def on_click(e):
                    sucesso, msg = ApiClient.excluir_usuario(uid)
                    page.snack_bar = ft.SnackBar(ft.Text(msg, color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600 if sucesso else ft.colors.RED_600)
                    page.snack_bar.open = True
                    carregar_dados_funcionarios()
                    carregar_dados()
                    page.update()
                return on_click

            lista_funcionarios.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(u['nome'], weight="bold", color="#333333"),
                            ft.Text(f"Usuário: {u['username']} | Perfil: {u['perfil']}", color="#555555", size=12)
                        ], expand=True),
                        ft.IconButton(icon=ft.icons.ACCOUNT_BALANCE, icon_color=COR_VERMELHO_ESCURO, tooltip="Banco de Horas", on_click=abrir_banco(u['id'], u['nome'])),
                        ft.IconButton(icon=ft.icons.PICTURE_AS_PDF, icon_color=COR_LARANJA, tooltip="Exportar PDF", on_click=abrir_pdf(u['id'], u['nome'])),
                        ft.IconButton(icon=ft.icons.LOCK_RESET, icon_color=ft.colors.BLUE_700, tooltip="Redefinir Senha", on_click=abrir_senha(u['id'])),
                        ft.IconButton(icon=ft.icons.DELETE_FOREVER, icon_color=ft.colors.RED_600, tooltip="Excluir", on_click=excluir_func(u['id']))
                    ]), bgcolor="#f5f5f5", padding=10, border_radius=8
                )
            )
        page.update()

    dialog_funcionarios = ft.AlertDialog(
        modal=True, 
        title=ft.Row([
            ft.Text("Gestão de Funcionários", color=COR_TEXTO_CLARO, weight="bold"),
            ft.IconButton(icon=ft.icons.PERSON_ADD, icon_color=COR_LARANJA, tooltip="Cadastrar Novo", on_click=abrir_modal_novo_user)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        content=ft.Container(content=lista_funcionarios, width=650),
        actions=[ft.TextButton("Fechar", on_click=lambda e: setattr(dialog_funcionarios, 'open', False) or page.update())]
    )

    def abrir_modal_funcionarios(e):
        page.dialog = dialog_funcionarios
        dialog_funcionarios.open = True
        carregar_dados_funcionarios()
        page.update()

    def criar_card(titulo, controle_valor):
        return ft.Container(
            content=ft.Column([ft.Text(titulo, size=14, color="#555555", weight="bold"), controle_valor], alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=COR_TEXTO_CLARO, width=200, height=100, padding=20, border_radius=15, shadow=SOMBRA_MODERNA
        )

    cards_row = ft.Row([criar_card("Total de Funcionários", lbl_total_usuarios), criar_card("Registros Exibidos", lbl_total_registros)], alignment=ft.MainAxisAlignment.START)
    threading.Thread(target=carregar_dados, daemon=True).start()

    # ---- MODAL APROVAÇÕES PENDENTES ----
    lista_ajustes = ft.ListView(height=300, spacing=10)

    def carregar_ajustes():
        lista_ajustes.controls.clear()
        pendentes = ApiClient.obter_ajustes_pendentes()
        if not pendentes:
            lista_ajustes.controls.append(ft.Text("Nenhum ajuste pendente.", color="#333333"))
        
        for a in pendentes:
            def criar_evento_resolver(ajuste_id):
                def on_click(e):
                    ApiClient.resolver_ajuste(ajuste_id, e.control.data)
                    dialog_ajustes_admin.open = False
                    page.snack_bar = ft.SnackBar(ft.Text("Solicitação processada com sucesso!", color=COR_TEXTO_CLARO), bgcolor=ft.colors.GREEN_600)
                    page.snack_bar.open = True
                    carregar_dados()
                    page.update()
                return on_click
                
            lista_ajustes.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{a['funcionario']} - {a['data']}", weight="bold", color="#333333"),
                        ft.Text(f"Quer registrar: {a['tipo']} às {a['hora']}", color="#555555"),
                        ft.Text(f"Motivo: {a['motivo']}", color="#555555", italic=True),
                        ft.Row([
                            ft.ElevatedButton("Aprovar", data="aprovar", bgcolor=ft.colors.GREEN_600, color=COR_TEXTO_CLARO, on_click=criar_evento_resolver(a['id'])),
                            ft.ElevatedButton("Rejeitar", data="rejeitar", bgcolor=ft.colors.RED_600, color=COR_TEXTO_CLARO, on_click=criar_evento_resolver(a['id']))
                        ])
                    ]), bgcolor="#f5f5f5", padding=10, border_radius=8
                )
            )
        page.update()

    dialog_ajustes_admin = ft.AlertDialog(
        modal=True, title=ft.Text("Aprovações Pendentes", color=COR_TEXTO_CLARO, weight="bold"),
        content=ft.Container(content=lista_ajustes, width=450),
        actions=[ft.TextButton("Fechar", on_click=lambda e: setattr(dialog_ajustes_admin, 'open', False) or page.update())]
    )
    
    def abrir_modal_ajustes(e):
        page.dialog = dialog_ajustes_admin
        dialog_ajustes_admin.open = True
        carregar_ajustes()

    return ft.View(
        "/admin",
        [
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Image(src="logo.png", width=200, height=60, fit=ft.ImageFit.CONTAIN),
                        
                        ft.Row([
                            ft.ElevatedButton("Funcionários", icon=ft.icons.PEOPLE, bgcolor="#3d0000", color=COR_TEXTO_CLARO, on_click=abrir_modal_funcionarios),
                            ft.ElevatedButton("Aprovações", icon=ft.icons.FACT_CHECK, bgcolor="#3d0000", color=COR_TEXTO_CLARO, on_click=abrir_modal_ajustes),
                            ft.ElevatedButton("Meu Ponto", icon=ft.icons.FINGERPRINT, bgcolor="#333", color=COR_TEXTO_CLARO, on_click=lambda e: page.go("/employee")),
                            ft.IconButton(ft.icons.LOGOUT, icon_color=COR_TEXTO_CLARO, on_click=lambda e: page.go("/login"))
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Container(height=20),
                    cards_row,
                    ft.Container(height=20),
                    
                    ft.Row([
                        ft.Text("Registros de Ponto", size=18, weight="bold", color=COR_TEXTO_CLARO),
                        ft.Row([
                            lbl_data_filtro,
                            ft.IconButton(icon=ft.icons.CALENDAR_MONTH, icon_color=COR_LARANJA, tooltip="Escolher Dia", on_click=lambda _: date_picker.pick_date()),
                            ft.IconButton(icon=ft.icons.CLEAR, icon_color=ft.colors.RED_400, tooltip="Limpar Filtro", on_click=limpar_filtro)
                        ])
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(color="#a99590"),
                    
                    ft.Container(
                        content=lista_registros,
                        expand=True, bgcolor="#e2e8f0", border_radius=10, padding=10
                    )
                ]),
                gradient=GRADIENTE_FUNDO, expand=True, padding=30
            )
        ],
        padding=0
    )