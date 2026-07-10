"""REST API viewsets."""
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api.permissions import IsEditorOrReadOnly
from api.serializers import (
    ArticleDetailSerializer, ArticleListSerializer, ArticleWriteSerializer,
    AuthorSerializer, CategorySerializer, CommentSerializer, TagSerializer, UserSerializer,
)
from accounts.models import User
from authors.models import AuthorProfile
from categories.models import Category, Tag
from comments.models import Comment
from news.models import Article
from news.services import ArticleService
from search.services import SearchService


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.select_related('author', 'category').prefetch_related('tags')
    permission_classes = [IsEditorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'author', 'is_featured', 'is_breaking', 'province']
    search_fields = ['title', 'subtitle', 'excerpt', 'body']
    ordering_fields = ['published_at', 'view_count', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated or not self.request.user.can_edit_articles():
            qs = qs.filter(status='published', published_at__lte=timezone.now())
        return qs

    def perform_create(self, serializer):
        article = serializer.save(created_by=self.request.user)
        ArticleService.prepare_article(article)
        article.save()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        ArticleService.transition_status(article, 'published', request.user)
        return Response({'status': 'published'})

    @action(detail=False, methods=['get'])
    def trending(self, request):
        articles = ArticleService.get_published().order_by('-view_count')[:10]
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'

    @action(detail=False, methods=['get'])
    def trending(self, request):
        tags = Tag.objects.filter(is_trending=True).order_by('-usage_count')[:20]
        return Response(TagSerializer(tags, many=True).data)


class AuthorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuthorProfile.objects.all()
    serializer_class = AuthorSerializer
    lookup_field = 'slug'


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('article', 'user')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.can_moderate_comments():
            qs = qs.filter(status='approved')
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='approved')


class SearchViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        query = request.query_params.get('q', '')
        filters = {
            'category': request.query_params.get('category'),
            'author': request.query_params.get('author'),
            'province': request.query_params.get('province'),
            'sort': request.query_params.get('sort', '-published_at'),
        }
        results = SearchService.search(query, filters)[:50]
        return Response(ArticleListSerializer(results, many=True).data)

    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        return Response({'results': SearchService.autocomplete(request.query_params.get('q', ''))})


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAdminUser]

    def list(self, request):
        from analytics.services import AnalyticsService
        return Response({
            'stats': AnalyticsService.get_dashboard_stats(),
            'charts': AnalyticsService.get_chart_data(),
        })


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
