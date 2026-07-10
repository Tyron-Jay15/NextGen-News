"""Comment URL patterns."""
from django.urls import path

from comments import views

app_name = 'comments'

urlpatterns = [
    path('post/<slug:slug>/', views.post_comment, name='post'),
    path('vote/<int:pk>/', views.vote_comment, name='vote'),
    path('report/<int:pk>/', views.report_comment, name='report'),
]
