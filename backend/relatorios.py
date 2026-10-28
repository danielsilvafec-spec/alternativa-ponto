# backend/relatorios.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

def gerar_relatorio_mensal(nome_funcionario: str, mes: str, registros: list) -> str:
    nome_arquivo = f"relatorio_{nome_funcionario.replace(' ', '_')}_{mes}.pdf"
    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elementos = []
    estilos = getSampleStyleSheet()
    
    # Cabeçalho
    elementos.append(Paragraph(f"<b>Relatório de Ponto - {nome_funcionario}</b>", estilos['Title']))
    elementos.append(Paragraph(f"Mês de Referência: {mes}", estilos['Normal']))
    elementos.append(Spacer(1, 20))
    
    # Dados da Tabela
    dados = [["Data e Hora", "Tipo de Marcação", "Coordenadas (GPS)"]]
    for reg in registros:
        data_formatada = reg['data_hora'][:19].replace('T', ' ')
        loc = f"Lat: {reg['lat']}, Lng: {reg['lng']}" if reg['lat'] else "Sem GPS"
        dados.append([data_formatada, reg['tipo'], loc])
        
    tabela = Table(dados, colWidths=[150, 150, 200])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#710000")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f4f7f6")),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    
    elementos.append(tabela)
    doc.build(elementos)
    
    return nome_arquivo