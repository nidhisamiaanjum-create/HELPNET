from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [

    path('admin/', admin.site.urls),

    path(
        'api/auth/',
        include('apps.users.urls')
    ),

    path(
        '',
        TemplateView.as_view(
            template_name='pages/home.html'
        ),
        name='home'
    ),

    path(
        'login/',
        TemplateView.as_view(
            template_name='pages/login.html'
        ),
        name='login'
    ),
    path(
        'register/',
        TemplateView.as_view(
            template_name='pages/register.html'
        ),
        name='register'
    ),
    path(
        'dashboard/',
        TemplateView.as_view(
            template_name='pages/dashboard.html'
        ),
        name='dashboard'
    ),
]