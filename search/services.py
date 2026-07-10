"""Search services."""
from django.db.models import Q

from news.models import Article
from news.services import ArticleService


class SearchService:
    @staticmethod
    def search(query: str, filters: dict = None):
        filters = filters or {}
        qs = ArticleService.get_published()

        if query:
            qs = qs.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(body__icontains=query) |
                Q(tags__name__icontains=query) |
                Q(author__display_name__icontains=query)
            ).distinct()

        if filters.get('category'):
            qs = qs.filter(category__slug=filters['category'])
        if filters.get('author'):
            qs = qs.filter(author__slug=filters['author'])
        if filters.get('tag'):
            qs = qs.filter(tags__slug=filters['tag'])
        if filters.get('province'):
            qs = qs.filter(province__icontains=filters['province'])
        if filters.get('municipality'):
            qs = qs.filter(municipality__icontains=filters['municipality'])
        if filters.get('date_from'):
            qs = qs.filter(published_at__date__gte=filters['date_from'])
        if filters.get('date_to'):
            qs = qs.filter(published_at__date__lte=filters['date_to'])

        sort = filters.get('sort') or '-published_at'
        if sort == 'popularity':
            sort = '-view_count'
        elif sort == 'comments':
            sort = '-comment_count'

        return qs.order_by(sort)

    @staticmethod
    def autocomplete(query: str, limit: int = 10) -> list[dict]:
        if len(query) < 2:
            return []
        articles = ArticleService.get_published().filter(
            Q(title__icontains=query) | Q(subtitle__icontains=query)
        )[:limit]
        return [{'title': a.title, 'url': a.get_absolute_url(), 'type': 'article'} for a in articles]
