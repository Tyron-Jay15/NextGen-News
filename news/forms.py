"""News forms."""
from django import forms

from news.models import Article, NewsletterSubscriber


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = [
            'title', 'subtitle', 'excerpt', 'body', 'hero_image', 'hero_image_caption', 'video_url',
            'author', 'category', 'tags', 'article_type', 'province', 'municipality',
            'is_featured', 'is_breaking', 'is_editors_pick', 'is_sticky', 'allow_comments',
            'seo_title', 'seo_description', 'seo_keywords', 'scheduled_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitle': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hero_image_caption': forms.TextInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...',
            }),
            'author': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'article_type': forms.Select(attrs={'class': 'form-select'}),
            'province': forms.TextInput(attrs={'class': 'form-control'}),
            'municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'seo_title': forms.TextInput(attrs={'class': 'form-control'}),
            'seo_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'seo_keywords': forms.TextInput(attrs={'class': 'form-control'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your email'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your name (optional)'}),
        }
