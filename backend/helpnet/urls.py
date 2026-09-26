from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse
from apps.users.views import PublicUserProfileView

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
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/goods/', include('apps.goods.urls')),
    path('api/health/', include('apps.health.urls')),
    path('api/volunteer/', include('apps.volunteer.urls')),
    path('api/users/<uuid:user_id>/', PublicUserProfileView.as_view(), name='public-user-profile'),

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
    path('notifications/', TemplateView.as_view(template_name='pages/notifications.html'), name='notifications'),
    path('goods-list/', TemplateView.as_view(template_name='pages/goods-list.html'), name='goods-list-page'),
    path('create-goods/', TemplateView.as_view(template_name='pages/create-goods.html'), name='create-goods-page'),
    path('goods-details/', TemplateView.as_view(template_name='pages/goods-details.html'), name='goods-details-page'),
    path('health-questions/', TemplateView.as_view(template_name='pages/health-questions.html'), name='health-questions-page'),
    path('create-health-question/', TemplateView.as_view(template_name='pages/create-health-question.html'), name='create-health-question-page'),
    path('health-question-details/', TemplateView.as_view(template_name='pages/health-question-details.html'), name='health-question-details-page'),
    path('health-professionals/', TemplateView.as_view(template_name='pages/health-professionals.html'), name='health-professionals-page'),
    path('volunteer-opportunities/', TemplateView.as_view(template_name='pages/volunteer-opportunities.html'), name='volunteer-opportunities-page'),
    path('create-opportunity/', TemplateView.as_view(template_name='pages/create-opportunity.html'), name='create-opportunity-page'),
    path('volunteer-profile/', TemplateView.as_view(template_name='pages/volunteer-profile.html'), name='volunteer-profile-page'),
    path('volunteer-attendance/', TemplateView.as_view(template_name='pages/volunteer-attendance.html'), name='volunteer-attendance-page'),
    path('volunteer-message/', TemplateView.as_view(template_name='pages/volunteer-message.html'), name='volunteer-message-page'),
    path('volunteer-certificate/', TemplateView.as_view(template_name='pages/volunteer-certificate.html'), name='volunteer-certificate-page'),
    path('volunteer-search/', TemplateView.as_view(template_name='pages/volunteer-search.html'), name='volunteer-search-page'),
    path('admin-volunteers/', TemplateView.as_view(template_name='pages/admin-volunteers.html'), name='admin-volunteers-page'),
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
