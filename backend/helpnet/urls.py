from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse

def root_view(request):
    return JsonResponse({
        "message": "Welcome to HELPNET API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "auth": "/api/auth/"
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', root_view, name="api-root"),
    path('api/auth/', include('apps.users.urls')),

    path('',           TemplateView.as_view(template_name='pages/home.html'),       name='home'),
    path('login/',     TemplateView.as_view(template_name='pages/login.html'),      name='login'),
    path('register/',  TemplateView.as_view(template_name='pages/register.html'),   name='register'),
    path('dashboard/', TemplateView.as_view(template_name='pages/dashboard.html'),  name='dashboard'),
    path('profile/',   TemplateView.as_view(template_name='pages/profile.html'),    name='profile'),

    path(
        'nid-verification/',
        TemplateView.as_view(template_name='pages/nid-verification.html'),
        name='nid-verification',
    ),
    path(
        'admin-verification/',
        TemplateView.as_view(template_name='pages/admin-verification.html'),
        name='admin-verification',
    ),
    path(
        'admin-logs/',
        TemplateView.as_view(template_name='pages/admin-logs.html'),
        name='admin-logs',
    ),
       path(
    'admin-dashboard/',
    TemplateView.as_view(
        template_name='pages/admin-dashboard.html'
    ),
    name='admin-dashboard',
    ),

    # API endpoints the JS will call (create later in apps/verification/urls.py)
    path("verification/", include("apps.verification.urls")),

 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)