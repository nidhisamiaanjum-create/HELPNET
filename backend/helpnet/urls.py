from django.contrib import admin
from django.urls import path, include
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
    path('api/waste/', include('apps.waste.urls')),
    path('api/farmer/', include('apps.farmer.urls')),
    path('api/ratings/', include('apps.ratings.urls')),
    path('api/reports/', include('apps.reports.urls')),

    path('',           TemplateView.as_view(template_name='pages/home.html'),       name='home'),
    path('login/',     TemplateView.as_view(template_name='pages/login.html'),      name='login'),
    path('register/',  TemplateView.as_view(template_name='pages/register.html'),   name='register'),
    path('dashboard/', TemplateView.as_view(template_name='pages/dashboard.html'),  name='dashboard'),
    path('profile/',   TemplateView.as_view(template_name='pages/profile.html'),    name='profile'),

    # Waste Pickup & Collector pages
    path('waste-pickup/', TemplateView.as_view(template_name='pages/waste-pickup.html'), name='waste-pickup'),
    path('collector-details/', TemplateView.as_view(template_name='pages/collector-details.html'), name='collector-details'),

    # Farmer Marketplace pages
    path('farmer-market/', TemplateView.as_view(template_name='pages/farmer-market.html'), name='farmer-market'),
    path('create-produce/', TemplateView.as_view(template_name='pages/create-produce.html'), name='create-produce'),
    path('produce-details/', TemplateView.as_view(template_name='pages/produce-details.html'), name='produce-details'),

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

    # API endpoints the JS will call (create later in apps/verification/urls.py)
    path("verification/", include("apps.verification.urls")),
]