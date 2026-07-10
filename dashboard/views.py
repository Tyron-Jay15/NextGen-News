"""Dashboard views."""
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from analytics.services import AnalyticsService
from comments.models import Comment
from news.models import Article, NewsSource
from news.scrapers.service import NewsScraperService
from news.services import ArticleService


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or self.request.user.role_name in (
                'super_admin', 'admin', 'chief_editor', 'editor', 'reporter',
                'photographer', 'contributor', 'moderator'
            )
        )


class DashboardHomeView(LoginRequiredMixin, StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['stats'] = AnalyticsService.get_dashboard_stats()
        ctx['chart_data'] = json.dumps(AnalyticsService.get_chart_data())
        ctx['recent_articles'] = Article.objects.order_by('-updated_at')[:10]
        ctx['pending_comments'] = Comment.objects.filter(status='pending').count()
        ctx['news_sources'] = NewsSource.objects.filter(is_active=True).count()
        ctx['scraped_articles'] = Article.objects.filter(is_scraped=True).count()
        return ctx


class DashboardArticleListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Article
    template_name = 'dashboard/articles.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        qs = Article.objects.select_related('author', 'category').order_by('-updated_at')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


@login_required
def article_workflow(request, pk, action):
    if not request.user.can_edit_articles():
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:articles')
    article = get_object_or_404(Article, pk=pk)
    try:
        ArticleService.transition_status(article, action, request.user)
        messages.success(request, f'Article status updated to {action}.')
    except ValueError as e:
        messages.error(request, str(e))
    return redirect('dashboard:articles')


class CommentModerationView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    model = Comment
    template_name = 'dashboard/comments.html'
    context_object_name = 'comments'
    paginate_by = 20

    def get_queryset(self):
        return Comment.objects.filter(status='pending').select_related('article', 'user')


@login_required
def moderate_comment(request, pk, action):
    if not request.user.can_moderate_comments():
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:comments')
    comment = get_object_or_404(Comment, pk=pk)
    if action in ('approved', 'rejected', 'spam'):
        comment.status = action
        comment.save()
        if action == 'approved':
            from django.db.models import F
            Article.objects.filter(pk=comment.article_id).update(comment_count=F('comment_count') + 1)
        messages.success(request, f'Comment {action}.')
    return redirect('dashboard:comments')


@login_required
@require_POST
def run_news_scraper(request):
    if not request.user.is_staff and request.user.role_name not in ('super_admin', 'admin', 'chief_editor'):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:home')
    result = NewsScraperService.scrape_all()
    messages.success(
        request,
        f'Scraper finished: {result["created"]} verified article(s) published, '
        f'{result["rejected"]} rejected by credibility scan, {result["skipped"]} skipped.',
    )
    return redirect('dashboard:home')
