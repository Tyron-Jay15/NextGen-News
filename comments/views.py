"""Comment views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from comments.forms import CommentForm
from comments.models import Comment, CommentReport, CommentVote
from comments.services import create_public_comment
from config.utils import get_client_ip
from news.models import Article


@ratelimit(key='ip', rate='10/h', method='POST', block=True)
@require_POST
def post_comment(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    if not article.allow_comments:
        messages.error(request, 'Comments are disabled for this article.')
        return redirect(article.get_absolute_url())

    form = CommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Invalid comment.')
        return redirect(article.get_absolute_url())

    parent = None
    parent_id = request.POST.get('parent_id')
    if parent_id:
        parent = get_object_or_404(Comment, pk=parent_id, article=article)

    create_public_comment(
        article=article,
        body=form.cleaned_data['body'],
        ip_address=get_client_ip(request),
        parent=parent,
    )
    messages.success(request, 'Comment posted.')
    return redirect(article.get_absolute_url())


@login_required
@require_POST
def vote_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    vote_type = request.POST.get('vote_type')
    if vote_type not in ('like', 'dislike'):
        return JsonResponse({'error': 'Invalid vote'}, status=400)
    CommentVote.objects.update_or_create(
        comment=comment, user=request.user, defaults={'vote_type': vote_type}
    )
    likes = comment.votes.filter(vote_type='like').count()
    dislikes = comment.votes.filter(vote_type='dislike').count()
    comment.likes = likes
    comment.dislikes = dislikes
    comment.save(update_fields=['likes', 'dislikes'])
    return JsonResponse({'likes': likes, 'dislikes': dislikes})


@login_required
@require_POST
def report_comment(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    reason = request.POST.get('reason', 'Reported as abusive')
    CommentReport.objects.create(comment=comment, reported_by=request.user, reason=reason)
    messages.success(request, 'Comment reported. Thank you.')
    return redirect(comment.article.get_absolute_url())
