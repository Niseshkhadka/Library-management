from django.contrib import admin
from django.urls import path,include
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('', lambda request: redirect('login-page')),
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]