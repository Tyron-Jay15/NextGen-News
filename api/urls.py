"""REST API URL configuration."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from api import views

app_name = 'api'

router = DefaultRouter()
router.register(r'articles', views.ArticleViewSet, basename='article')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'search', views.SearchViewSet, basename='search')
router.register(r'analytics', views.AnalyticsViewSet, basename='analytics')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
