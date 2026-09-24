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
    path('api/ratings/', include('apps.ratings.urls')),
    path('api/blood/', include('apps.blood.urls')),

    path('',           TemplateView.as_view(template_name='pages/home.html'),       name='home'),
    path('login/',     TemplateView.as_view(template_name='pages/login.html'),      name='login'),
    path(
    'forgot-password/',
    TemplateView.as_view(
        template_name='pages/forgot-password.html'
    ),
    name='forgot-password',
),
    path(
    'reset-password/',
    TemplateView.as_view(
        template_name='pages/reset-password.html'
    ),
    name='reset-password',
),
    path('register/',  TemplateView.as_view(template_name='pages/register.html'),   name='register'),
    path('dashboard/', TemplateView.as_view(template_name='pages/dashboard.html'),  name='dashboard'),
    path('profile/',   TemplateView.as_view(template_name='pages/profile.html'),    name='profile'),
    path('ratings/',   TemplateView.as_view(template_name='pages/ratings.html'),    name='ratings'),
    path('blood/',     TemplateView.as_view(template_name='pages/blood.html'),      name='blood'),
    path('blood-donor/', TemplateView.as_view(template_name='pages/blood.html'), name='blood-donor'),
    path('blood-request/', TemplateView.as_view(template_name='pages/blood.html'), name='blood-request'),
    path('blood-requests/', TemplateView.as_view(template_name='pages/blood.html'), name='blood-requests'),
    path('matching-donors/', TemplateView.as_view(template_name='pages/blood.html'), name='matching-donors'),
    path('donation-history/', TemplateView.as_view(template_name='pages/blood.html'), name='donation-history'),

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
    path("api/verification/", include("apps.verification.urls")),

    

 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)