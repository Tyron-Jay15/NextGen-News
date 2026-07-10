"""PDF generation utility."""
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def generate_article_pdf(article) -> HttpResponse:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(article.title, styles['Title']),
        Spacer(1, 12),
        Paragraph(f'By {article.author.display_name if article.author else "Staff"}', styles['Normal']),
        Spacer(1, 24),
    ]
    import re
    body_text = re.sub(r'<[^>]+>', '', article.body)
    for para in body_text.split('\n\n'):
        if para.strip():
            story.append(Paragraph(para.strip(), styles['Normal']))
            story.append(Spacer(1, 12))
    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{article.slug}.pdf"'
    return response
