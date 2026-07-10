"""News URL patterns."""
from django.urls import path

from news import views

app_name = 'news'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    path('articles/<slug:slug>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('articles/<slug:slug>/pdf/', views.ArticlePDFView.as_view(), name='article_pdf'),
    path('articles/<slug:slug>/bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('articles/<slug:slug>/share/', views.ShareArticleView.as_view(), name='share_article'),
    path('category/<slug:slug>/', views.CategoryNewsView.as_view(), name='category'),
    path('tag/<slug:slug>/', views.TagNewsView.as_view(), name='tag'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('sample-images/<slug:slug>.jpg', views.sample_hero_image, name='sample_image'),
    path('sample-images/<slug:slug>/', views.sample_hero_image, name='sample_image_alt'),
    path('create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('edit/<int:pk>/', views.ArticleUpdateView.as_view(), name='article_edit'),
]
