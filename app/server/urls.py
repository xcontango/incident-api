from django.urls import path

from .views import IncidentViewSet


urlpatterns = [
    path('incidents', IncidentViewSet.as_view(), name="incidents"),
]
