"""Comment posting helpers."""
import random

from django.db.models import F

from comments.models import Comment
from news.models import Article


def generate_anonymous_name() -> str:
    """Return a random display name like anonymous4821."""
    for _ in range(20):
        name = f'anonymous{random.randint(100, 99999)}'
        if not Comment.objects.filter(author_name=name).exists():
            return name
    return f'anonymous{random.randint(100000, 999999)}'


def create_public_comment(article: Article, body: str, ip_address: str | None = None, parent=None) -> Comment:
    """Create an anonymous public comment and publish it immediately."""
    comment = Comment.objects.create(
        article=article,
        body=body,
        author_name=generate_anonymous_name(),
        author_email='',
        user=None,
        is_guest=True,
        status='approved',
        ip_address=ip_address,
        parent=parent,
    )
    Article.objects.filter(pk=article.pk).update(comment_count=F('comment_count') + 1)
    return comment
