# pylint: disable=missing-docstring
from django.conf.urls import url

from openedx.core.djangoapps.programs.api.v1 import views


urlpatterns = [
    url(r'^certify/$', views.IssueProgramCertificatesView.as_view(), name='certify'),
]
