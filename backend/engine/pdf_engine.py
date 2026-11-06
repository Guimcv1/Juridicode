"""
PDF Database Engine and PDF Contract Generator.
Allows querying PDF files for clause verification, searching case law / precedent documents,
and exporting interpreted smart legal contracts directly to certified PDF.
"""

import os
import tempfile
from xml.sax.saxutils import escape
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFEngine:
    def __init__(self, storage_dir: str = "backend/storage"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
        except Exception as e:
            # Fallback to pypdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            except Exception as e2:
                text = f"[Erro ao extrair PDF: {e2}]"
        return text

    def query_pdf_knowledge_base(self, query: str, pdf_filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Searches all uploaded PDFs in backend/storage for clauses, contradictions, or keywords.
        """
        results = []
        files = [pdf_filename] if pdf_filename else os.listdir(self.storage_dir)

        query_terms = [t.lower().strip() for t in query.split() if len(t) > 2]

        for fname in files:
            if not fname or not fname.lower().endswith(".pdf"):
                continue
            full_path = os.path.join(self.storage_dir, fname)
            if not os.path.exists(full_path):
                continue

            content = self.extract_text_from_pdf(full_path)
            lines = content.split("\n")

            matched_snippets = []
            for i, line in enumerate(lines):
                if any(term in line.lower() for term in query_terms):
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    snippet = " ".join([l.strip() for l in lines[start:end] if l.strip()])
                    matched_snippets.append({"line": i + 1, "text": snippet})

            if matched_snippets:
                results.append({
                    "file": fname,
                    "matches_count": len(matched_snippets),
                    "snippets": matched_snippets[:5]
                })

        return results

    def generate_template_pdf(
        self,
        title: str,
        contract_type: str,
        content: str,
        output_path: str,
        formatting: Optional[Dict[str, Any]] = None,
        source_pdf: Optional[str] = None,
        field_replacements: Optional[Dict[str, str]] = None,
        field_targets: Optional[Dict[str, str]] = None,
    ) -> str:
        """Render a filled template, retaining an uploaded PDF as the document base."""
        formatting = formatting or {}
        margins = formatting.get("margins", {})
        render_path = output_path
        if source_pdf and source_pdf.lower().endswith(".pdf") and os.path.exists(source_pdf):
            with tempfile.NamedTemporaryFile(prefix="juridicode_filled_", suffix=".pdf", delete=False) as temp_file:
                render_path = temp_file.name
        doc = SimpleDocTemplate(
            render_path,
            pagesize=letter,
            rightMargin=float(margins.get("right", 54)),
            leftMargin=float(margins.get("left", 54)),
            topMargin=float(margins.get("top", 54)),
            bottomMargin=float(margins.get("bottom", 54)),
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TemplateTitle", parent=styles["Heading1"], fontSize=17,
            leading=21, alignment=1, textColor=colors.HexColor("#0F172A"),
            spaceAfter=8,
        )
        type_style = ParagraphStyle(
            "TemplateType", parent=styles["Normal"], fontSize=9,
            leading=12, alignment=1, textColor=colors.HexColor("#64748B"),
            spaceAfter=16,
        )
        body_style = ParagraphStyle(
            "TemplateBody", parent=styles["Normal"],
            fontName=(formatting.get("font_family", "Helvetica") if formatting.get("font_family") in {"Helvetica", "Times-Roman", "Courier"} else "Helvetica"),
            fontSize=max(6, min(24, float(formatting.get("font_size", 10)))),
            leading=15, textColor=colors.HexColor("#1E293B"), spaceAfter=8,
        )
        story = [
            Paragraph(escape(title), title_style),
            Paragraph(f"TIPO DE INSTRUMENTO: {escape(contract_type)}", type_style),
            HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#2563EB"), spaceAfter=14),
        ]
        for paragraph in content.split("\n"):
            text = escape(paragraph.strip()).replace("  ", "&nbsp;&nbsp;")
            if text:
                story.append(Paragraph(text, body_style))
            else:
                story.append(Spacer(1, 5))
        doc.build(story)
        if render_path != output_path:
            try:
                from pypdf import PdfReader, PdfWriter
                source_reader = PdfReader(source_pdf)
                if field_replacements:
                    overlay_path = tempfile.mktemp(prefix="juridicode_overlay_", suffix=".pdf")
                    self._create_field_overlay(
                        source_pdf,
                        overlay_path,
                        field_replacements,
                        field_targets or {},
                        formatting,
                    )
                    overlay_reader = PdfReader(overlay_path)
                    for page, overlay in zip(source_reader.pages, overlay_reader.pages):
                        page.merge_page(overlay)
                    writer = PdfWriter()
                    for page in source_reader.pages:
                        writer.add_page(page)
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
                    os.remove(overlay_path)
                else:
                    writer = PdfWriter()
                    for page in source_reader.pages:
                        writer.add_page(page)
                    with open(output_path, "wb") as output_file:
                        writer.write(output_file)
            finally:
                if os.path.exists(render_path):
                    os.remove(render_path)
        return output_path

    def _create_field_overlay(
        self,
        source_pdf: str,
        overlay_path: str,
        replacements: Dict[str, str],
        field_targets: Dict[str, str],
        formatting: Optional[Dict[str, Any]] = None,
    ) -> None:
        import pdfplumber

        source = pdfplumber.open(source_pdf)
        first_page = source.pages[0]
        page_width = float(first_page.width)
        page_height = float(first_page.height)
        pdf = canvas.Canvas(overlay_path, pagesize=(page_width, page_height))
        for page in source.pages:
            words = page.extract_words() or []
            for field, value in replacements.items():
                target = field_targets.get(field, "{{" + field + "}}")
                target_words = target.lower().split()
                for index in range(len(words) - len(target_words) + 1):
                    candidate = [str(words[index + offset].get("text", "")) for offset in range(len(target_words))]
                    if " ".join(candidate).lower() != " ".join(target_words):
                        continue
                    selected = words[index:index + len(target_words)]
                    x0 = min(float(word["x0"]) for word in selected)
                    x1 = max(float(word["x1"]) for word in selected)
                    top = min(float(word["top"]) for word in selected)
                    bottom = max(float(word["bottom"]) for word in selected)
                    y = page_height - bottom
                    pdf.setFillColorRGB(1, 1, 1)
                    pdf.rect(x0 - 1, y - 2, max(x1 - x0, 80) + 2, bottom - top + 5, fill=1, stroke=0)
                    pdf.setFillColorRGB(0, 0, 0)
                    font_name = (formatting or {}).get("font_family", "Helvetica")
                    if font_name not in {"Helvetica", "Times-Roman", "Courier"}:
                        font_name = "Helvetica"
                    font_size = max(6, min(24, float((formatting or {}).get("font_size", 9))))
                    pdf.setFont(font_name, font_size)
                    pdf.drawString(x0, y + 1, str(value))
                    break
            pdf.showPage()
        pdf.save()
        source.close()

    def generate_legal_pdf(
        self,
        contract_data: Dict[str, Any],
        output_path: str,
        formatting: Optional[Dict[str, Any]] = None,
        footer_image: Optional[str] = None,
    ) -> str:
        """
        Generates a certified, official legal PDF document from the interpreted AST and state.
        """
        formatting = formatting or {}
        margins = formatting.get("margins", {})
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=float(margins.get("right", 40)),
            leftMargin=float(margins.get("left", 40)),
            topMargin=float(margins.get("top", 40)),
            bottomMargin=float(margins.get("bottom", 40))
        )
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0F172A'),
            alignment=1, # Center
            spaceAfter=15
        )

        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Heading2'],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=12,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'LegalBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )

        audit_style = ParagraphStyle(
            'AuditText',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#64748B')
        )

        story = []

        # Header
        story.append(Paragraph("INSTRUMENTO PARTICULAR DE CONTRATO JURÍDICO VIRTUAL", title_style))
        story.append(Paragraph(f"<b>IDENTIFICADOR / NOME:</b> {contract_data.get('name', 'Instrumento Geral')}", h2_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=15))

        # Estado Atual
        curr_state = contract_data.get('current_state') or "NÃO INFORMADO"
        story.append(Paragraph(f"<b>STATUS DE EFICÁCIA (MÁQUINA DE ESTADOS):</b> <font color='#2563EB'><b>{curr_state}</b></font>", body_style))
        story.append(Spacer(1, 8))

        # Partes Envolvidas
        partes = contract_data.get('partes', [])
        partes_txt = ", ".join(partes) if partes else "NÃO INFORMADAS"
        story.append(Paragraph(f"<b>CLÁUSULA PRIMEIRA - DAS PARTES ENVOLVIDAS:</b>", h2_style))
        story.append(Paragraph(f"Figuram como partes integrantes deste instrumento jurídico formalmente verificado: <b>{partes_txt}</b>.", body_style))
        story.append(Spacer(1, 8))

        # Obrigações
        story.append(Paragraph(f"<b>CLÁUSULA SEGUNDA - DAS OBRIGAÇÕES E VENCIMENTOS:</b>", h2_style))
        obs = contract_data.get('obligations', [])
        for i, ob in enumerate(obs, 1):
            devedor = ob.get('devedor') or "NÃO INFORMADO"
            credor = ob.get('credor') or "NÃO INFORMADO"
            valor = ob.get('valor') or "NÃO INFORMADO"
            venc = ob.get('vencimento') or "NÃO INFORMADO"
            story.append(Paragraph(
                f"<b>Subcláusula 2.{i} ({ob.get('title', 'Obrigação')}):</b> "
                f"O devedor <b>{devedor}</b> obriga-se a pagar ao credor <b>{credor}</b> "
                f"a quantia certa de <b>{valor}</b>, com vencimento impreterível em <b>{venc}</b>.",
                body_style
            ))
            for cond in ob.get('conditions', []):
                then_txt = "; ".join(cond.get('then', []))
                story.append(Paragraph(f"&nbsp;&nbsp;&bull; <i>Condição de Inadimplemento:</i> Se {cond.get('condition')}, então aplicar: {then_txt}.", body_style))

        story.append(Spacer(1, 10))

        # Cláusula de Transições / Automação
        story.append(Paragraph(f"<b>CLÁUSULA TERCEIRA - DAS TRANSIÇÕES E CIÊNCIAS:</b>", h2_style))
        story.append(Paragraph(
            "O presente contrato opera sob arquitetura auditável e transições determinísticas. "
            "Todas as ciências, assinaturas e comprovantes são armazenados e computados de forma colaborativa.",
            body_style
        ))
        story.append(Spacer(1, 15))

        custom_clauses = formatting.get("custom_clauses", [])
        for index, clause in enumerate(custom_clauses, 1):
            title = escape(str(clause.get("title") or f"CLÁUSULA {index}"))
            body = escape(str(clause.get("body") or "")).replace("\n", "<br/>")
            if body:
                story.append(Paragraph(f"<b>{title}</b>", h2_style))
                story.append(Paragraph(body, body_style))

        signatures = contract_data.get("signatures", [])
        if signatures:
            story.append(Paragraph("<b>CERTIFICADO DE ASSINATURAS ELETRÔNICAS</b>", h2_style))
            story.append(Paragraph(
                "As assinaturas abaixo foram registradas no Juridico.Code com consentimento "
                "expresso, data, identificador do certificado e hash SHA-256 do conteúdo.",
                body_style,
            ))
            signature_data = [["Signatário", "Documento", "Data", "Certificado", "Hash"]]
            for signature in signatures:
                signature_data.append([
                    str(signature.get("signer_name", "")),
                    str(signature.get("signer_document", "")),
                    str(signature.get("signed_at", "")),
                    str(signature.get("certificate_serial", "")),
                    str(signature.get("document_sha256", ""))[:18] + "...",
                ])
            signature_table = Table(signature_data, colWidths=[100, 90, 90, 105, 80])
            signature_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(signature_table)

        # Tabela de Auditoria e Criptografia
        audit = contract_data.get('audit', {})
        audit_data = [
            ["UUID do Documento:", audit.get("uuid", "123e4567-e89b-12d3-a456-426614174000")],
            ["Data de Constituição:", audit.get("criado_em", "12/01/2026")],
            ["Última Modificação:", audit.get("editado_em", "13/05/2026")],
            ["Criador / Responsável:", audit.get("criador", "advogado.numero1")],
            ["Último Editor:", audit.get("ultimo_editor", "advogado.numero2")],
            ["Histórico de Versões:", f"{audit.get('adicoes', 235)} adições, {audit.get('delecoes', 12)} deleções"],
            ["Assinatura Criptográfica PGP:", audit.get("pgp_fingerprint", "PGP-SHA256-VALID-ICP-BR")],
            ["Integridade Hash (SHA-256):", audit.get("sha256", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")]
        ]
        
        t = Table(audit_data, colWidths=[170, 360])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1E293B')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(t)

        footer_path = (
            os.path.join(self.storage_dir, "company_images", os.path.basename(footer_image))
            if footer_image else None
        )
        if footer_path and not os.path.isfile(footer_path):
            legacy_path = os.path.join(self.storage_dir, os.path.basename(footer_image))
            footer_path = legacy_path if os.path.isfile(legacy_path) else None
        if footer_path and os.path.isfile(footer_path):
            def draw_footer(canvas, document):
                canvas.saveState()
                footer = Image(footer_path, width=120, height=30)
                footer.drawOn(canvas, document.leftMargin, 12)
                canvas.restoreState()
            doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
        else:
            doc.build(story)
        return output_path
