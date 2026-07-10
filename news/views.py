"""News public and editorial views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from advertisements.services import AdService
from analytics.services import AnalyticsService
from categories.models import Category
from comments.models import Comment
from comments.forms import CommentForm
from news.forms import ArticleForm, NewsletterForm
from news.models import Article, Bookmark, NewsletterSubscriber
from news.services import AIService, ArticleService, BookmarkService, ReadingHistoryService


class HomeView(ListView):
    template_name = 'news/home.html'
    context_object_name = 'latest_articles'

    def get_queryset(self):
        return ArticleService.get_published().order_by('-published_at')[:12]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        homepage = ArticleService.get_homepage_articles()
        ctx.update(homepage)
        ctx['categories'] = Category.objects.filter(is_active=True, parent__isnull=True)[:8]
        ctx['sidebar_ads'] = AdService.get_ads_for_placement('homepage_sidebar')
        ctx['banner_ads'] = AdService.get_ads_for_placement('homepage_top')
        ctx['newsletter_form'] = NewsletterForm()
        return ctx


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'article'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        qs = Article.objects.select_related('author', 'category').prefetch_related('tags', 'media_items')
        if self.request.user.is_authenticated and self.request.user.can_edit_articles():
            return qs
        return qs.filter(status='published', published_at__isnull=False)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        article = self.object
        if article.status == 'published':
            article.increment_views()
            AnalyticsService.log_article_view(request, article)
            ReadingHistoryService.record(request.user, article)
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        article = self.object
        ctx['related_articles'] = ArticleService.get_related(article)
        ctx['prev_article'], ctx['next_article'] = ArticleService.get_prev_next(article)
        ctx['popular_articles'] = ArticleService.get_published().order_by('-view_count')[:5]
        ctx['comments'] = Comment.objects.filter(article=article, status='approved', parent__isnull=True)
        ctx['comment_form'] = CommentForm()
        ctx['ai_summary'] = AIService.generate_summary(article)
        ctx['is_bookmarked'] = False
        if self.request.user.is_authenticated:
            ctx['is_bookmarked'] = Bookmark.objects.filter(user=self.request.user, article=article).exists()
        ctx['sidebar_ads'] = AdService.get_ads_for_placement('article_sidebar')
        ctx['inline_ads'] = AdService.get_ads_for_placement('article_inline')
        return ctx


class CategoryNewsView(ListView):
    template_name = 'news/category.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return ArticleService.get_published().filter(
            Q(category=self.category) | Q(category__parent=self.category)
        ).order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category'] = self.category
        return ctx


class TagNewsView(ListView):
    template_name = 'news/tag.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        from categories.models import Tag
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return ArticleService.get_published().filter(tags=self.tag).order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tag'] = self.tag
        return ctx


class ArticleListView(ListView):
    template_name = 'news/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        return ArticleService.get_published().order_by('-published_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['list_type'] = self.kwargs.get('list_type', 'latest')
        ctx['page_title'] = self.kwargs.get('list_type', 'Latest News').replace('-', ' ').title()
        return ctx


class ArticleCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/article_form.html'
    success_url = reverse_lazy('dashboard:articles')

    def test_func(self):
        return self.request.user.can_edit_articles()

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        article = form.save(commit=False)
        ArticleService.prepare_article(article)
        article.save()
        form.save_m2m()
        ArticleService.save_revision(article, self.request.user, 'Initial creation')
        messages.success(self.request, 'Article saved as draft.')
        return redirect('news:article_edit', pk=article.pk)


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'news/article_form.html'

    def test_func(self):
        return self.request.user.can_edit_articles()

    def form_valid(self, form):
        article = form.save(commit=False)
        ArticleService.prepare_article(article)
        article.save()
        form.save_m2m()
        ArticleService.save_revision(article, self.request.user, 'Updated article')
        messages.success(self.request, 'Article updated.')
        return redirect('news:article_edit', pk=article.pk)


@login_required
@require_POST
def toggle_bookmark(request, slug):
    article = get_object_or_404(Article, slug=slug)
    bookmarked = BookmarkService.toggle(request.user, article)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'bookmarked': bookmarked})
    messages.success(request, 'Bookmark updated.')
    return redirect(article.get_absolute_url())


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Thank you for subscribing!')
    else:
        messages.error(request, 'Invalid email address.')
    return redirect(request.META.get('HTTP_REFERER', 'news:home'))


class ArticlePDFView(DetailView):
    model = Article
    slug_field = 'slug'

    def get(self, request, *args, **kwargs):
        from news.utils import generate_article_pdf
        article = self.get_object()
        return generate_article_pdf(article)


class ShareArticleView(View):
    def post(self, request, slug):
        article = get_object_or_404(Article, slug=slug)
        Article.objects.filter(pk=article.pk).update(share_count=article.share_count + 1)
        return JsonResponse({'share_count': article.share_count + 1})
