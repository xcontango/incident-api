from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('api/v1/', include('server.urls')),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='api/v1/incidents', permanent=False)),
]
