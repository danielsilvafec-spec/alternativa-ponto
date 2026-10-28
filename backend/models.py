# backend/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(String, nullable=False) # admin ou funcionario
    departamento = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

class RegistroPonto(Base):
    __tablename__ = "registros_ponto"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    data_hora = Column(String, nullable=False) # Formato ISO
    tipo = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    hash_integridade = Column(String, nullable=False)
    data_criacao = Column(DateTime(timezone=True), server_default=func.now())

# Adicione no final de backend/models.py

class Jornada(Base):
    __tablename__ = "jornadas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    horas_diarias = Column(Float, default=8.0)
    entrada_padrao = Column(String, default="08:00")
    saida_padrao = Column(String, default="18:00")
    minutos_intervalo = Column(Integer, default=60)

class ApuracaoDiaria(Base):
    __tablename__ = "apuracoes_diarias"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    data = Column(String, nullable=False) # AAAA-MM-DD
    minutos_trabalhados = Column(Integer, default=0)
    minutos_excedentes = Column(Integer, default=0) # Horas extras
    status = Column(String, default="pendente") # pendente, aprovado, rejeitado

class SolicitacaoAjuste(Base):
    __tablename__ = "solicitacoes_ajuste"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    data = Column(String, nullable=False)
    hora_correta = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    motivo = Column(String)
    status = Column(String, default="pendente")