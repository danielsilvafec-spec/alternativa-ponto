# backend/motor_calculo.py
import datetime
import models

def processar_apuracao_diaria(db, user_id: int, data: str):
    # 1. Buscar a jornada configurada ou usar 8 horas padrão
    jornada = db.query(models.Jornada).filter(models.Jornada.user_id == user_id).first()
    minutos_esperados = int(jornada.horas_diarias * 60) if jornada else 480 

    # 2. Buscar todos os registros do funcionário no dia, ordenados pela hora
    registros = db.query(models.RegistroPonto).filter(
        models.RegistroPonto.user_id == user_id,
        models.RegistroPonto.data_hora.like(f"{data}%")
    ).order_by(models.RegistroPonto.data_hora.asc()).all()

    if not registros:
        return None

    minutos_trabalhados = 0

    # 3. Lógica em Pares: Soma a diferença de tempo de cada par (Entrada -> Saída)
    # Ex: (Entrada até Saída Intervalo) + (Ret. Intervalo até Saída Final)
    for i in range(0, len(registros) - 1, 2):
        entrada = datetime.datetime.fromisoformat(registros[i].data_hora)
        saida = datetime.datetime.fromisoformat(registros[i+1].data_hora)
        delta = saida - entrada
        minutos_trabalhados += int(delta.total_seconds() / 60)

    # 4. Cálculo do saldo (Excedente = Extra | Negativo = Atraso/Falta)
    minutos_excedentes = minutos_trabalhados - minutos_esperados

    # 5. Salva ou atualiza a Apuração Diária no Banco de Dados
    apuracao = db.query(models.ApuracaoDiaria).filter(
        models.ApuracaoDiaria.user_id == user_id,
        models.ApuracaoDiaria.data == data
    ).first()

    if not apuracao:
        apuracao = models.ApuracaoDiaria(user_id=user_id, data=data)
        db.add(apuracao)

    apuracao.minutos_trabalhados = minutos_trabalhados
    apuracao.minutos_excedentes = minutos_excedentes
    apuracao.status = "pendente"
    
    db.commit()
    return apuracao