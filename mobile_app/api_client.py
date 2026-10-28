# mobile_app/api_client.py
import requests

BASE_URL = "http://127.0.0.1:8000/api"

class ApiClient:
    token = None
    user_data = None

    @classmethod
    def get_headers(cls):
        return {"Authorization": f"Bearer {cls.token}"} if cls.token else {}

    @classmethod
    def login(cls, username, password):
        try:
            response = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password})
            if response.status_code == 200:
                data = response.json()
                cls.token = data.get("access_token")
                cls.user_data = data.get("user")
                return True, "Login bem-sucedido"
            return False, "Usuário ou senha incorretos."
        except Exception:
            return False, "Erro de conexão com o servidor."

    @classmethod
    def bater_ponto(cls, tipo, lat, lng):
        try:
            payload = {"tipo": tipo, "latitude": lat, "longitude": lng}
            response = requests.post(f"{BASE_URL}/ponto/registrar", json=payload, headers=cls.get_headers())
            if response.status_code == 200:
                return True, response.json().get("mensagem")
            return False, "Erro ao registrar ponto."
        except Exception:
            return False, "Sem conexão."

    @classmethod
    def obter_historico_hoje(cls):
        try:
            response = requests.get(f"{BASE_URL}/ponto/hoje", headers=cls.get_headers())
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    @classmethod
    def obter_usuarios_admin(cls):
        try:
            response = requests.get(f"{BASE_URL}/admin/usuarios", headers=cls.get_headers())
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    @classmethod
    def obter_registros_admin(cls, data_filtro=None):
        try:
            url = f"{BASE_URL}/admin/registros"
            if data_filtro:
                url += f"?data={data_filtro}"
            response = requests.get(url, headers=cls.get_headers())
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    @classmethod
    def obter_banco_de_horas(cls):
        try:
            response = requests.get(f"{BASE_URL}/admin/banco_de_horas", headers=cls.get_headers())
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    @classmethod
    def criar_usuario(cls, dados_usuario):
        try:
            response = requests.post(f"{BASE_URL}/admin/usuarios", json=dados_usuario, headers=cls.get_headers())
            if response.status_code == 200:
                return True, response.json().get("mensagem")
            else:
                return False, response.json().get("detail", "Erro ao criar usuário")
        except Exception:
            return False, "Sem conexão com o servidor."

    @classmethod
    def obter_jornada(cls, user_id):
        try:
            response = requests.get(f"{BASE_URL}/admin/jornada/{user_id}", headers=cls.get_headers())
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    @classmethod
    def configurar_jornada(cls, dados_jornada):
        try:
            response = requests.post(f"{BASE_URL}/admin/jornada", json=dados_jornada, headers=cls.get_headers())
            if response.status_code == 200:
                return True, response.json().get("mensagem")
            return False, "Erro ao configurar jornada."
        except Exception:
            return False, "Sem conexão com o servidor."

    @classmethod
    def apurar_horas(cls, user_id, data):
        try:
            response = requests.get(f"{BASE_URL}/admin/apuracao/{user_id}/{data}", headers=cls.get_headers())
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    @classmethod
    def baixar_relatorio_pdf(cls, user_id, mes):
        try:
            response = requests.get(f"{BASE_URL}/admin/relatorio/{user_id}/{mes}", headers=cls.get_headers(), stream=True)
            if response.status_code == 200:
                nome_arquivo = f"Relatorio_Ponto_{mes}.pdf"
                with open(nome_arquivo, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, f"PDF salvo na pasta do App: {nome_arquivo}"
            elif response.status_code == 404:
                return False, "Nenhum ponto registrado nesse mês."
            else:
                return False, "Erro ao gerar o relatório."
        except Exception:
            return False, "Sem conexão com o servidor."

    @classmethod
    def solicitar_ajuste(cls, dados):
        res = requests.post(f"{BASE_URL}/ponto/ajuste", json=dados, headers=cls.get_headers())
        return res.status_code == 200

    @classmethod
    def obter_ajustes_pendentes(cls):
        res = requests.get(f"{BASE_URL}/admin/ajustes", headers=cls.get_headers())
        return res.json() if res.status_code == 200 else []

    @classmethod
    def resolver_ajuste(cls, ajuste_id, acao):
        res = requests.post(f"{BASE_URL}/admin/ajustes/{ajuste_id}/{acao}", headers=cls.get_headers())
        return res.status_code == 200

    @classmethod
    def alterar_senha_usuario(cls, user_id, nova_senha):
        try:
            headers = {"Authorization": f"Bearer {cls.token}"}
            response = requests.put(
                f"{BASE_URL}/admin/usuarios/{user_id}/senha", # AQUI: Apenas BASE_URL e sem o /api duplicado
                json={"nova_senha": nova_senha},
                headers=headers
            )
            if response.status_code == 200:
                return True, response.json()["mensagem"]
            return False, response.json().get("detail", "Erro ao alterar senha.")
        except requests.exceptions.RequestException:
            return False, "Erro de conexão com o servidor."

    @classmethod
    def excluir_usuario(cls, user_id):
        try:
            res = requests.delete(f"{BASE_URL}/admin/usuarios/{user_id}", headers=cls.get_headers())
            if res.status_code == 200:
                return True, res.json().get("mensagem", "Funcionário excluído com sucesso!")
            return False, res.json().get("detail", "Erro ao excluir funcionário.")
        except Exception:
            return False, "Sem conexão com o servidor."