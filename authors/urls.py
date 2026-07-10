"""Author URL patterns."""
from django.urls import path

from authors import views

app_name = 'authors'

urlpatterns = [
    path('', views.AuthorListView.as_view(), name='list'),
    path('<slug:slug>/', views.AuthorDetailView.as_view(), name='detail'),
]
