"""Dashboard URL patterns."""
from django.urls import path

from dashboard import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('articles/', views.DashboardArticleListView.as_view(), name='articles'),
    path('articles/<int:pk>/workflow/<str:action>/', views.article_workflow, name='article_workflow'),
    path('comments/', views.CommentModerationView.as_view(), name='comments'),
    path('comments/<int:pk>/<str:action>/', views.moderate_comment, name='moderate_comment'),
    path('scraper/run/', views.run_news_scraper, name='run_scraper'),
]
