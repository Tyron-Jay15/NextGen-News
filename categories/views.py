"""Category views."""
from django.views.generic import DetailView, ListView

from categories.models import Category
from news.services import ArticleService


class CategoryListView(ListView):
    model = Category
    template_name = 'categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children')


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'categories/detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['articles'] = ArticleService.get_published().filter(category=self.object).order_by('-published_at')[:12]
        ctx['subcategories'] = self.object.children.filter(is_active=True)
        return ctx
