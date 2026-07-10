"""Author views."""
from django.views.generic import DetailView, ListView

from authors.models import AuthorProfile
from news.services import ArticleService


class AuthorListView(ListView):
    model = AuthorProfile
    template_name = 'authors/list.html'
    context_object_name = 'authors'

    def get_queryset(self):
        return AuthorProfile.objects.all().order_by('display_name')


class AuthorDetailView(DetailView):
    model = AuthorProfile
    template_name = 'authors/detail.html'
    context_object_name = 'author'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['articles'] = ArticleService.get_published().filter(author=self.object).order_by('-published_at')
        return ctx
