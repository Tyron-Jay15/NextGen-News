"""Search views."""
from django.http import JsonResponse
from django.views.generic import ListView

from search.forms import SearchForm
from search.services import SearchService


class SearchView(ListView):
    template_name = 'search/results.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.form = SearchForm(self.request.GET)
        if self.form.is_valid():
            return SearchService.search(
                self.form.cleaned_data.get('q', ''),
                self.form.cleaned_data,
            )
        return SearchService.search('')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['query'] = self.request.GET.get('q', '')
        return ctx


def autocomplete_api(request):
    query = request.GET.get('q', '')
    results = SearchService.autocomplete(query)
    return JsonResponse({'results': results})
