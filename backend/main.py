# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel
import datetime
import hashlib
import jwt

import models, database, auth
from relatorios import gerar_relatorio_mensal
from motor_calculo import processar_apuracao_diaria

# Cria as tabelas
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Alternativa Ponto API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def criar_admin_padrao():
    db = database.SessionLocal()
    admin_existe = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin_existe:
        novo_admin = models.User(
            nome_completo="Administrador Geral",
            username="admin",
            senha_hash=auth.hash_password("admin123"),
            perfil="admin",
            departamento="TI"
        )
        db.add(novo_admin)
        db.commit()
    db.close()

criar_admin_padrao()

# Dependência para pegar o usuário logado pelo Token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

# ---- MODELOS PYDANTIC ----
class LoginRequest(BaseModel):
    username: str
    password: str

class PontoRequest(BaseModel):
    tipo: str
    latitude: float
    longitude: float

class UserCreateRequest(BaseModel):
    nome_completo: str
    username: str
    senha: str
    perfil: str
    departamento: str
    horas_diarias: float = 8.0
    entrada_padrao: str = "08:00"
    saida_padrao: str = "18:00"
    minutos_intervalo: int = 60

class JornadaRequest(BaseModel):
    user_id: int
    horas_diarias: float
    entrada_padrao: str
    saida_padrao: str
    minutos_intervalo: int

class AjusteRequest(BaseModel):
    data: str
    hora_correta: str
    tipo: str
    motivo: str

class NovaSenhaRequest(BaseModel):
    nova_senha: str

# ---- ROTAS DE AUTENTICAÇÃO E PONTO ----
@app.post("/api/login")
def login(request: LoginRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.username == request.username).first()
    if not user or not auth.verify_password(request.password, user.senha_hash) or not user.ativo:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    token_data = {"sub": user.username, "id": user.id, "perfil": user.perfil}
    access_token = auth.create_access_token(data=token_data)

    return {"access_token": access_token, "user": {"id": user.id, "nome_completo": user.nome_completo, "perfil": user.perfil}}

@app.post("/api/ponto/registrar")
def registrar_ponto(ponto: PontoRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    agora = datetime.datetime.now().isoformat()
    
    dados_hash = f"{current_user.id}{agora}{ponto.tipo}mobile_app".encode('utf-8')
    hash_int = hashlib.sha256(dados_hash).hexdigest()

    novo_registro = models.RegistroPonto(
        user_id=current_user.id,
        data_hora=agora,
        tipo=ponto.tipo,
        latitude=ponto.latitude,
        longitude=ponto.longitude,
        hash_integridade=hash_int
    )
    db.add(novo_registro)
    db.commit()
    
    return {"sucesso": True, "mensagem": f"{ponto.tipo} registrado!"}

@app.get("/api/ponto/hoje")
def registros_hoje(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    hoje = datetime.date.today().isoformat()
    registros = db.query(models.RegistroPonto).filter(
        models.RegistroPonto.user_id == current_user.id,
        models.RegistroPonto.data_hora.like(f"{hoje}%")
    ).order_by(models.RegistroPonto.data_hora.desc()).all()
    
    return [{"tipo": r.tipo, "data_hora": r.data_hora, "is_ajuste": (r.hash_integridade == "ajuste_manual")} for r in registros]

# ---- ROTAS DO ADMINISTRADOR ----
@app.get("/api/admin/usuarios")
def listar_usuarios(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    usuarios = db.query(models.User).filter(models.User.perfil != "excluido").all()
    return [{"id": u.id, "nome": u.nome_completo, "username": u.username, "perfil": u.perfil, "ativo": u.ativo} for u in usuarios]

@app.post("/api/admin/usuarios")
def criar_usuario(user_in: UserCreateRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    usuario_existente = db.query(models.User).filter(models.User.username == user_in.username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Nome de usuário já está em uso.")
    
    novo_user = models.User(
        nome_completo=user_in.nome_completo,
        username=user_in.username,
        senha_hash=auth.hash_password(user_in.senha),
        perfil=user_in.perfil,
        departamento=user_in.departamento
    )
    db.add(novo_user)
    db.commit()
    db.refresh(novo_user)

    if novo_user.perfil == "funcionario":
        nova_jornada = models.Jornada(
            user_id=novo_user.id,
            horas_diarias=user_in.horas_diarias,
            entrada_padrao=user_in.entrada_padrao,
            saida_padrao=user_in.saida_padrao,
            minutos_intervalo=user_in.minutos_intervalo
        )
        db.add(nova_jornada)
        db.commit()
    
    return {"sucesso": True, "mensagem": "Funcionário e jornada cadastrados com sucesso!"}

@app.put("/api/admin/usuarios/{user_id}/senha")
def alterar_senha_admin(user_id: int, request: NovaSenhaRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    user.senha_hash = auth.hash_password(request.nova_senha)
    db.commit()
    return {"sucesso": True, "mensagem": "Senha atualizada com sucesso!"}

@app.delete("/api/admin/usuarios/{user_id}")
def excluir_usuario(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    user.username = f"excluido_{user.id}_{user.username}"
    user.senha_hash = "bloqueado"
    user.perfil = "excluido" 
    
    db.commit()
    return {"mensagem": "Funcionário excluído e histórico preservado!"}

@app.get("/api/admin/registros")
def listar_todos_registros(data: str = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = db.query(models.RegistroPonto, models.User.nome_completo).join(models.User, models.RegistroPonto.user_id == models.User.id)
    
    if data:
        query = query.filter(models.RegistroPonto.data_hora.like(f"{data}%"))
        
    resultados = query.order_by(models.RegistroPonto.data_hora.desc()).limit(50).all()
    
    return [{
        "id": reg.id, 
        "funcionario": nome, 
        "tipo": reg.tipo, 
        "data_hora": reg.data_hora, 
        "lat": reg.latitude, 
        "lng": reg.longitude,
        "is_ajuste": (reg.hash_integridade == "ajuste_manual")
    } for reg, nome in resultados]

@app.get("/api/admin/banco_de_horas")
def relatorio_banco_horas(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    usuarios = db.query(models.User).filter(models.User.perfil == "funcionario").all()
    resultado = []
    
    for u in usuarios:
        total_minutos = db.query(func.sum(models.ApuracaoDiaria.minutos_excedentes)).filter(models.ApuracaoDiaria.user_id == u.id).scalar() or 0
        horas = abs(total_minutos) // 60
        minutos = abs(total_minutos) % 60
        sinal = "+" if total_minutos >= 0 else "-"
        resultado.append({
            "nome": u.nome_completo,
            "saldo": f"{sinal} {horas}h {minutos}m",
            "positivo": total_minutos >= 0
        })
        
    return resultado

@app.post("/api/admin/jornada")
def configurar_jornada(jornada_in: JornadaRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    jornada = db.query(models.Jornada).filter(models.Jornada.user_id == jornada_in.user_id).first()
    if not jornada:
        jornada = models.Jornada(user_id=jornada_in.user_id)
        db.add(jornada)
        
    jornada.horas_diarias = jornada_in.horas_diarias
    jornada.entrada_padrao = jornada_in.entrada_padrao
    jornada.saida_padrao = jornada_in.saida_padrao
    jornada.minutos_intervalo = jornada_in.minutos_intervalo
    db.commit()
    
    return {"sucesso": True, "mensagem": "Jornada configurada com sucesso!"}

@app.get("/api/admin/jornada/{user_id}")
def obter_jornada(user_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    jornada = db.query(models.Jornada).filter(models.Jornada.user_id == user_id).first()
    if not jornada:
        return {"horas_diarias": 8.0, "entrada_padrao": "08:00", "saida_padrao": "18:00", "minutos_intervalo": 60}
    return {
        "horas_diarias": jornada.horas_diarias,
        "entrada_padrao": jornada.entrada_padrao,
        "saida_padrao": jornada.saida_padrao,
        "minutos_intervalo": jornada.minutos_intervalo
    }

@app.get("/api/admin/apuracao/{user_id}/{data}")
def obter_apuracao(user_id: int, data: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    apuracao = processar_apuracao_diaria(db, user_id, data)
    
    if not apuracao:
        return {"sucesso": False, "mensagem": "Nenhum ponto registrado nesse dia."}
    
    horas_t = apuracao.minutos_trabalhados // 60
    min_t = apuracao.minutos_trabalhados % 60
    
    horas_e = abs(apuracao.minutos_excedentes) // 60
    min_e = abs(apuracao.minutos_excedentes) % 60
    sinal = "+" if apuracao.minutos_excedentes >= 0 else "-"
    
    return {
        "sucesso": True,
        "trabalhado": f"{horas_t}h {min_t}m",
        "saldo": f"{sinal} {horas_e}h {min_e}m",
        "status": apuracao.status
    }

@app.get("/api/admin/relatorio/{user_id}/{mes}")
def baixar_relatorio(user_id: int, mes: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
    registros = db.query(models.RegistroPonto).filter(
        models.RegistroPonto.user_id == user_id,
        models.RegistroPonto.data_hora.like(f"{mes}%")
    ).order_by(models.RegistroPonto.data_hora.asc()).all()
    
    if not registros:
        raise HTTPException(status_code=404, detail="Sem registros neste mês.")
        
    lista_dicts = [{"data_hora": r.data_hora, "tipo": r.tipo, "lat": r.latitude, "lng": r.longitude} for r in registros]
    
    caminho_pdf = gerar_relatorio_mensal(user.nome_completo, mes, lista_dicts)
    return FileResponse(path=caminho_pdf, filename=caminho_pdf, media_type='application/pdf')

# ---- ROTAS DE AJUSTES MANUAIS ----
@app.post("/api/ponto/ajuste")
def solicitar_ajuste(ajuste: AjusteRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    novo_ajuste = models.SolicitacaoAjuste(user_id=current_user.id, data=ajuste.data, hora_correta=ajuste.hora_correta, tipo=ajuste.tipo, motivo=ajuste.motivo)
    db.add(novo_ajuste)
    db.commit()
    return {"sucesso": True, "mensagem": "Ajuste solicitado."}

@app.get("/api/admin/ajustes")
def listar_ajustes_pendentes(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin": 
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    ajustes = db.query(models.SolicitacaoAjuste, models.User.nome_completo).join(
        models.User, models.SolicitacaoAjuste.user_id == models.User.id
    ).filter(models.SolicitacaoAjuste.status == "pendente").all()
    
    return [{"id": a.id, "funcionario": nome, "data": a.data, "hora": a.hora_correta, "tipo": a.tipo, "motivo": a.motivo, "user_id": a.user_id} for a, nome in ajustes]

@app.post("/api/admin/ajustes/{ajuste_id}/{acao}")
def resolver_ajuste(ajuste_id: int, acao: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.perfil != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
        
    ajuste = db.query(models.SolicitacaoAjuste).filter(models.SolicitacaoAjuste.id == ajuste_id).first()
    
    if acao == "aprovar":
        ajuste.status = "aprovado"
        data_hora_iso = f"{ajuste.data}T{ajuste.hora_correta}:00"
        novo_ponto = models.RegistroPonto(user_id=ajuste.user_id, data_hora=data_hora_iso, tipo=ajuste.tipo, latitude=0.0, longitude=0.0, hash_integridade="ajuste_manual")
        db.add(novo_ponto)
        db.commit()
        processar_apuracao_diaria(db, ajuste.user_id, ajuste.data)
    else:
        ajuste.status = "rejeitado"
        db.commit()
    return {"sucesso": True}