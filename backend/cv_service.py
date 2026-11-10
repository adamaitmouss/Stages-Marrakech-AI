import io
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepTogether, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab
from pypdf import PdfReader
from .validation import text, email, safe_url

SECTIONS = {
    'education': 'Formation', 'experience': 'Expériences professionnelles', 'projects': 'Projets',
    'certifications': 'Certifications',
}


def validate_cv(data):
    if not isinstance(data, dict):
        raise ValueError('Profil CV invalide.')
    result = {}
    limits={'name':120,'title':200,'email':254,'phone':80,'city':120,'summary':6000,'technical':2000,'soft':2000,'languages':1000,'linkedin':500,'github':500}
    for field in ('name', 'title', 'email', 'phone', 'city', 'summary', 'technical', 'soft', 'languages', 'linkedin', 'github'):
        result[field] = text(data.get(field, ''), limits[field])
    if not result['name'] or not result['title']:
        raise ValueError('Nom et titre professionnel obligatoires.')
    if result['email']:
        result['email'] = email(result['email'])
    for field in ('linkedin', 'github'):
        if result[field] and not safe_url(result[field]):
            raise ValueError('Les liens doivent commencer par https:// ou http://.')
    for section in SECTIONS:
        entries = data.get(section, [])
        if not isinstance(entries, list) or len(entries) > 30:
            raise ValueError('Section CV invalide ou trop longue.')
        result[section] = []
        for item in entries:
            if not isinstance(item, dict):
                raise ValueError('Entrée CV invalide.')
            entry = {k: text(item.get(k, ''), {'title':200,'organization':200,'period':100,'description':4000}[k]) for k in ('title', 'organization', 'period', 'description')}
            dates = re.findall(r'(?<!\d)(19\d{2}|20\d{2})(?:[-/.](0?[1-9]|1[0-2]))?(?!\d)', entry['period'])
            if len(dates) >= 2 and (int(dates[0][0]), int(dates[0][1] or 0)) > (int(dates[-1][0]), int(dates[-1][1] or 0)):
                raise ValueError('Une période CV ne peut pas se terminer avant sa date de début.')
            if any(entry.values()):
                result[section].append(entry)
    return result


def extract_pdf(content):
    if not content or len(content) > 5 * 1024 * 1024 or not content.startswith(b'%PDF-'):
        raise ValueError('PDF invalide ou supérieur à 5 Mo.')
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted or len(reader.pages) > 15 or not len(reader.pages):
            raise ValueError('PDF chiffré, vide ou supérieur à 15 pages.')
        value = '\n'.join((page.extract_text() or '') for page in reader.pages)[:40000]
    except Exception as exc:
        raise ValueError('PDF illisible, chiffré ou endommagé.') from exc
    if not value.strip():
        raise ValueError('Ce PDF ne contient pas de texte lisible. Renseignez votre profil manuellement (OCR non intégré).')
    return value


def make_pdf(data, template='modern'):
    data = validate_cv(data)
    if template not in ('modern', 'ats'):
        raise ValueError('Modèle de CV inconnu.')
    fonts = Path(reportlab.__file__).parent / 'fonts'
    if 'CV' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('CV', str(fonts / 'Vera.ttf')))
        pdfmetrics.registerFont(TTFont('CV-Bold', str(fonts / 'VeraBd.ttf')))
        pdfmetrics.registerFontFamily('CV', normal='CV', bold='CV-Bold', italic='CV', boldItalic='CV-Bold')
    output = io.BytesIO()
    accent = colors.HexColor('#215CF3' if template == 'modern' else '#16243A')
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CVBody', fontName='CV', fontSize=9, leading=14, spaceAfter=5, textColor=colors.HexColor('#26374C'), splitLongWords=True))
    styles.add(ParagraphStyle('CVName', parent=styles['CVBody'], fontName='CV-Bold', fontSize=25, leading=31, textColor=colors.white if template=='modern' else colors.HexColor('#102039'), spaceAfter=6))
    styles.add(ParagraphStyle('CVTitle', parent=styles['CVBody'], fontSize=13, leading=19, textColor=colors.HexColor('#AAC8FF') if template=='modern' else accent, spaceAfter=10))
    styles.add(ParagraphStyle('CVContact', parent=styles['CVBody'], textColor=colors.HexColor('#DFE9FA') if template=='modern' else colors.HexColor('#26374C')))
    styles.add(ParagraphStyle('CVSection', parent=styles['CVBody'], fontName='CV-Bold', fontSize=11, leading=17, textColor=accent, spaceBefore=13, spaceAfter=6, keepWithNext=True))
    styles.add(ParagraphStyle('CVEntry', parent=styles['CVBody'], fontName='CV-Bold', keepWithNext=True))
    def para(value, style='CVBody'):
        return Paragraph(escape(value).replace('\n', '<br/>'), styles[style])
    header = [para(data['name'], 'CVName'), para(data['title'], 'CVTitle')]
    contacts = '  |  '.join(data[k] for k in ('email', 'phone', 'city') if data[k])
    if contacts:
        header.append(para(contacts,'CVContact'))
    for k in ('linkedin', 'github'):
        if data[k]:
            header.append(para(data[k],'CVContact'))
    if template=='modern':
        band=Table([[header]],colWidths=[A4[0]-86])
        band.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#11213D')),('LEFTPADDING',(0,0),(-1,-1),17),('RIGHTPADDING',(0,0),(-1,-1),17),('TOPPADDING',(0,0),(-1,-1),18),('BOTTOMPADDING',(0,0),(-1,-1),14)]))
        story=[band,Spacer(1,9)]
    else:
        story=header+[HRFlowable(width='100%',thickness=.5,color=accent,spaceBefore=9,spaceAfter=8)]
    if data['summary']:
        story += [para('Profil', 'CVSection'), para(data['summary'])]
    for key, label in SECTIONS.items():
        if data[key]:
            story.append(para(label, 'CVSection'))
            for item in data[key]:
                heading = ' - '.join(item[k] for k in ('title', 'organization', 'period') if item[k])
                if heading:
                    story.append(para(heading, 'CVEntry'))
                if item['description']:
                    story.append(para(item['description']))
                story.append(Spacer(1, 4))
    for key, label in [('technical', 'Compétences techniques'), ('soft', 'Compétences personnelles'), ('languages', 'Langues')]:
        if data[key]:
            story += [para(label, 'CVSection'), para(data[key])]
    def footer(canvas, doc):
        canvas.setFont('CV', 8)
        canvas.setFillColor(colors.HexColor('#6A7789'))
        canvas.drawRightString(A4[0]-43, 25, str(doc.page))
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=43, rightMargin=43, topMargin=38, bottomMargin=42,
                                 title=data['title'], author=data['name'], invariant=1)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
