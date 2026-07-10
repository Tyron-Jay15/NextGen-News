"""Account views."""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetDoneView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from accounts.forms import LoginForm, ProfileForm, RegisterForm, UserProfileForm
from accounts.models import User, UserProfile
from config.utils import get_client_ip


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        remember = form.cleaned_data.get('remember_me')
        if not remember:
            self.request.session.set_expiry(0)
        response = super().form_valid(form)
        user = form.get_user()
        user.last_login_ip = get_client_ip(self.request)
        user.save(update_fields=['last_login_ip'])
        messages.success(self.request, 'Welcome back!')
        return response


class UserLogoutView(LogoutView):
    next_page = 'news:home'


class UserRegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        from accounts.models import Role
        reader_role, _ = Role.objects.get_or_create(
            name='registered_reader',
            defaults={'display_name': 'Registered Reader'},
        )
        self.object.role = reader_role
        self.object.save()
        UserProfile.objects.get_or_create(user=self.object)
        messages.success(self.request, 'Account created! Please log in.')
        return response


class UserPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/emails/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = ProfileForm(request.POST, request.FILES, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        user_form = ProfileForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)
    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })


@login_required
def user_dashboard(request):
    from news.models import Bookmark, ReadingHistory
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('article')[:10]
    history = ReadingHistory.objects.filter(user=request.user).select_related('article')[:10]
    notifications = request.user.notifications.filter(is_read=False)[:5]
    staff_roles = (
        'super_admin', 'admin', 'chief_editor', 'editor', 'reporter',
        'photographer', 'contributor', 'moderator',
    )
    return render(request, 'accounts/user_dashboard.html', {
        'bookmarks': bookmarks,
        'history': history,
        'notifications': notifications,
        'show_staff_links': request.user.is_staff or request.user.role_name in staff_roles,
    })
