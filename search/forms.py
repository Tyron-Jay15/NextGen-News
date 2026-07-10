"""Search forms."""
from django import forms


class SearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Search news...', 'autocomplete': 'off',
    }))
    category = forms.CharField(required=False, widget=forms.HiddenInput())
    author = forms.CharField(required=False, widget=forms.HiddenInput())
    tag = forms.CharField(required=False, widget=forms.HiddenInput())
    province = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    municipality = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    sort = forms.ChoiceField(required=False, choices=[
        ('-published_at', 'Latest'),
        ('popularity', 'Most Popular'),
        ('comments', 'Most Commented'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))
