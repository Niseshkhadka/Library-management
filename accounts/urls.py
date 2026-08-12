from django.urls import path
from .views import RegisterView, LoginView, ProfileView, LibrarianOnlyTestView, PasswordResetRequestView, PasswordResetConfirmView, register_page, login_page, profile_page, logout_page, password_reset_request_page, password_reset_confirm_page, dashboard_page

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('test-librarian/', LibrarianOnlyTestView.as_view(), name='test-librarian'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('register-page/', register_page, name='register-page'),
    path('login-page/', login_page, name='login-page'),
    path('profile-page/', profile_page, name='profile-page'),
    path('logout-page/', logout_page, name='logout-page'),
    path('password-reset-page/', password_reset_request_page, name='password-reset-page'),
    path('password-reset-confirm-page/', password_reset_confirm_page, name='password-reset-confirm-page'),
    path('dashboard-page/', dashboard_page, name='dashboard-page'),
]
