import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_manual_pdf(output_path="DOCUMENTACAO_JURIDICO_CODE.pdf"):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=0
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#475569'),
        alignment=0
    )
    
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    story = []

    # Title
    story.append(Paragraph("Manual de Referência e Sintaxe", title_style))
    story.append(Paragraph("JURIDICO.CODE — A Linguagem Declarativa e Auditável do Meio Jurídico", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f172a'), spaceAfter=15))

    # Intro
    story.append(Paragraph("1. Introdução à Linguagem", h1_style))
    story.append(Paragraph(
        "O <b>Juridico.Code</b> é uma Domain-Specific Language (DSL) inspirada na clareza do COBOL e na robustez das máquinas de estado (FSM). "
        "Seu objetivo é transformar instrumentos jurídicos (contratos, termos, acordos e pareceres) em representações computacionais auditáveis, "
        "livres de ambiguidades ou contradições lógicas, com suporte nativo a simulação de obrigações e validação em tempo real.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # Tabela de Comandos
    story.append(Paragraph("2. Dicionário de Palavras-Chave e Comandos", h1_style))
    
    table_data = [
        [Paragraph("<b>Comando / Bloco</b>", body_style), Paragraph("<b>Finalidade e Descrição</b>", body_style), Paragraph("<b>Exemplo de Uso</b>", body_style)],
        [
            Paragraph("<b>CONTRATO</b>", code_style),
            Paragraph("Declara o início e o identificador do instrumento.", body_style),
            Paragraph("<code>CONTRATO CompraVenda</code>", code_style)
        ],
        [
            Paragraph("<b>ESTADO</b>", code_style),
            Paragraph("Define o estado inicial da máquina de estados (ex: RASCUNHO, ATIVO).", body_style),
            Paragraph("<code>ESTADO = RASCUNHO</code>", code_style)
        ],
        [
            Paragraph("<b>PARTES:</b>", code_style),
            Paragraph("Lista nominal das partes intervenientes separadas por vírgula.", body_style),
            Paragraph("<code>PARTES: COMPRADOR, VENDEDOR</code>", code_style)
        ],
        [
            Paragraph("<b>OBRIGAÇÃO</b>", code_style),
            Paragraph("Inicia bloco de prestação de dar, fazer ou pagar.", body_style),
            Paragraph("<code>OBRIGAÇÃO pagamento</code>", code_style)
        ],
        [
            Paragraph("<b>DEVEDOR: / CREDOR:</b>", code_style),
            Paragraph("Atribui polo passivo e polo ativo à obrigação.", body_style),
            Paragraph("<code>DEVEDOR: LOCATARIO<br/>CREDOR: LOCADOR</code>", code_style)
        ],
        [
            Paragraph("<b>VALOR: / VENCIMENTO:</b>", code_style),
            Paragraph("Parâmetros financeiros e termo de eficácia temporal.", body_style),
            Paragraph("<code>VALOR: R$ 50.000<br/>VENCIMENTO: 10/12/2026</code>", code_style)
        ],
        [
            Paragraph("<b>SE ... ENTÃO</b>", code_style),
            Paragraph("Gatilhos condicionais para aplicação de penalidades/juros.", body_style),
            Paragraph("<code>SE não_pago até VENCIMENTO<br/>ENTÃO APLICAR multa 2%</code>", code_style)
        ],
        [
            Paragraph("<b>TRANSIÇÃO</b>", code_style),
            Paragraph("Define mutação de estado baseada em pré-requisitos lógicos.", body_style),
            Paragraph("<code>TRANSIÇÃO ASSINADO:<br/>&nbsp;&nbsp;REQUER comprador.assinatura<br/>&nbsp;&nbsp;ENTÃO estado = ATIVO</code>", code_style)
        ],
        [
            Paragraph("<b>AUDITORIA</b>", code_style),
            Paragraph("Metadados criptográficos, UUID, autor e rastreabilidade.", body_style),
            Paragraph("<code>AUDITORIA DOCUMENTO:<br/>&nbsp;&nbsp;Criador: dr.silva<br/>&nbsp;&nbsp;UUID: 123e4567...</code>", code_style)
        ]
    ]

    t = Table(table_data, colWidths=[1.4*inch, 3.2*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Exemplo Prático
    story.append(Paragraph("3. Exemplo Prático de Código (.jur)", h1_style))
    sample_code = """CONTRATO PrestacaoServicosSoftware

ESTADO = RASCUNHO
PARTES: CONTRATANTE, CONTRATADA

OBRIGAÇÃO entrega_software
DEVEDOR: CONTRATADA
CREDOR: CONTRATANTE
VALOR: R$ 45.000
VENCIMENTO: 15/11/2026

SE não_pago até VENCIMENTO
ENTÃO
    APLICAR multa 10%
    E juros 1% ao mês

TRANSIÇÃO ASSINADO:
    REQUER contratante.assinatura
    REQUER contratada.assinatura
    ENTÃO
        estado = EM_EXECUCAO

TRANSIÇÃO FINALIZADO:
    REQUER estado = EM_EXECUCAO
    REQUER comprovante.pagamento
    ENTÃO
        estado = CONCLUIDO"""

    code_table = Table([[Paragraph(f"<pre>{sample_code}</pre>", code_style)]], colWidths=[7.1*inch])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(code_table)
    story.append(Spacer(1, 14))

    # Como Executar
    story.append(Paragraph("4. Como Executar via Linha de Comando (CLI)", h1_style))
    story.append(Paragraph(
        "Após a instalação, abra qualquer terminal e execute:",
        body_style
    ))
    cli_sample = "juris contrato.jur"
    cli_table = Table([[Paragraph(f"<b>&gt; {cli_sample}</b>", code_style)]], colWidths=[7.1*inch])
    cli_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(cli_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "O comando compilará a sintaxe, verificará contradições lógicas e abrirá automaticamente o dashboard visual no navegador.",
        body_style
    ))

    doc.build(story)
    print(f"[SUCESSO] Manual PDF gerado em: {output_path}")

if __name__ == "__main__":
    generate_manual_pdf()
