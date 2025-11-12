"""
URL configuration for betabank_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_control
import os


# Service Worker View
@require_GET
@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    """Serve the service worker from root"""
    sw_path = os.path.join(settings.BASE_DIR, "static", "service-worker.js")
    try:
        with open(sw_path, "r") as f:
            content = f.read()
        return HttpResponse(content, content_type="application/javascript")
    except FileNotFoundError:
        return HttpResponse("Service Worker not found", status=404)


urlpatterns = [
    path("service-worker.js", service_worker, name="service_worker"),
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("banking/", include("banking.urls")),
    path("transactions/", include("transactions.urls")),
    path("loans/", include("loans.urls")),
    path("investments/", include("investments.urls")),
    path("notifications/", include("notifications.urls")),
    # path("chat/", include("chat.urls")),
    path("manager/", include("manager.urls")),
    path("empty/", include("empty_routes.urls")),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
