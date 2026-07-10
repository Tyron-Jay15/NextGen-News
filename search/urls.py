"""Search URL patterns."""
from django.urls import path

from search import views

app_name = 'search'

urlpatterns = [
    path('', views.SearchView.as_view(), name='search'),
    path('autocomplete/', views.autocomplete_api, name='autocomplete'),
]
