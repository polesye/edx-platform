"""
OAuth2 wrapper urls
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from . import views


urlpatterns = patterns(
    '',
    #url(r'^authorize/?$', login_required(views.Capture.as_view()), name='capture'),
    #url(r'^authorize/confirm/?$', login_required(views.Authorize.as_view()), name='authorize'),
    #url(r'^redirect/?$', login_required(views.Redirect.as_view()), name='redirect'),
    url(r'^access_token/?$', csrf_exempt(views.AccessTokenView.as_view()), name='access_token'),
    #url(r'^access_token/(?P<token>[\w]+)/$', csrf_exempt(views.AccessTokenDetailView.as_view()), name='access_token_detail'),
    #url(r'^user_info/?$', csrf_exempt(views.UserInfoView.as_view()), name='user_info'),
)


