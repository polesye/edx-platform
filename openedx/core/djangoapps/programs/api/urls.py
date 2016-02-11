# pylint: disable=missing-docstring
from django.conf.urls import url, include


urlpatterns = [
    url(r'^v1/', include('openedx.core.djangoapps.programs.api.v1.urls', namespace='v1')),
]
