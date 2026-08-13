from django.http import request
from rest_framework import generics
from rest_framework.permissions import AllowAny
from .serializers import RegisterSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import LoginSerializer
from rest_framework.permissions import IsAuthenticated
from .serializers import UserProfileSerializer
from .permissions import IsLibrarianOrSuperAdmin
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from .models import User
from .forms import RegisterForm, LoginForm, ProfileForm, PasswordResetRequestForm, PasswordResetConfirmForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

class LibrarianOnlyTestView(APIView):
    permission_classes = [IsLibrarianOrSuperAdmin]

    def get(self, request):
        return Response({"message": f"Hello {request.user.username}, you have access!"})



class RegisterView(generics.CreateAPIView):
    queryset = None
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]  # anyone can register, even if not logged in




class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({
                "message": "Login successful",
                "username": user.username,
                "role": user.role
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists — security best practice
            return Response({"message": "If this email exists, a reset link has been sent."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = f"http://127.0.0.1:8000/api/accounts/password-reset-confirm/?uid={uid}&token={token}"

        send_mail(
            subject="Password Reset Request",
            message=f"Click the link to reset your password: {reset_link}",
            from_email="noreply@library.com",
            recipient_list=[email],
        )

        return Response({"message": "If this email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data['uid']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Invalid reset link"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful"})

def register_page(request):
     if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            return redirect('login-page')
     else:
        form = RegisterForm()

     return render(request, 'accounts/register.html', {'form': form})

def login_page(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard-page')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

@login_required(login_url='login-page')
def profile_page(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'user': request.user})

def logout_page(request):
    logout(request)
    return redirect('login-page')

def password_reset_request_page(request):
    sent = False
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(
                    f'/api/password-reset-confirm-page/?uid={uid}&token={token}'
                )
                send_mail(
                    subject="Password Reset Request",
                    message=f"Click the link to reset your password: {reset_link}",
                    from_email="noreply@library.com",
                    recipient_list=[email],
                )
            except User.DoesNotExist:
                pass  # don't reveal whether email exists
            sent = True
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset.html', {'form': form, 'sent': sent})


def password_reset_confirm_page(request):
    uid = request.GET.get('uid') or request.POST.get('uid')
    token = request.GET.get('token') or request.POST.get('token')
    success = False
    error = None

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=user_id)
                if default_token_generator.check_token(user, token):
                    user.set_password(form.cleaned_data['new_password'])
                    user.save()
                    success = True
                else:
                    error = "This reset link is invalid or has expired."
            except (User.DoesNotExist, ValueError, TypeError, OverflowError):
                error = "This reset link is invalid."
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'accounts/password_reset_confirm.html', {
        'form': form, 'uid': uid, 'token': token, 'success': success, 'error': error
    })

@login_required(login_url='login-page')
def dashboard_page(request):
    role = request.user.role
    context = {'user': request.user}

    if role == 'SUPERADMIN':
        return render(request, 'accounts/dashboard_superadmin.html', context)
    elif role == 'LIBRARIAN':
        return render(request, 'accounts/dashboard_librarian.html', context)
    else:
        return render(request, 'accounts/dashboard_member.html', context)