"""
Views that dispatch processing of OAuth requests to django-oauth2-provider or
django-oauth-toolkit as appropriate.
"""

from __future__ import unicode_literals

from django.views.generic import View
from edx_oauth2_provider import views as dop_views  # django-oauth2-provider views
from oauth2_provider import views as dot_views  # django-oauth-toolkit views
# from provider.oauth2.views import AccessTokenDetailView


DOT_BACKEND = object()
DOP_BACKEND = object()

class _DispatchingView(View):
    """
    Base class that route views to the appropriate provider view.
    """
    # pylint: disable=no-member

    def select_backend(self, request):
        """
        Given a request, return the appropriate OAuth handling library.

        This currently selects a backend based on a whitelist of client_ids,
        but this mechanism can be overridden as necessary for different views.
        """

        if request.POST['client_id'] in {'android', 'ios'}:
            return DOT_BACKEND
        else:
            return DOP_BACKEND

    def get_view_for_backend(self, backend):
        """
        Return the appropriate view from the requested backend.
        """
        if backend == DOT_BACKEND:
            return self.dot_view.as_view()
        elif backend == DOP_BACKEND:
            return self.dop_view.as_view()
        else:
            raise KeyError('Failed to dispatch view. Invalid backend {}'.format(backend))

    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch the request to the selected backend's view.
        """
        backend = self.select_backend(request)
        view = self.get_view_for_backend(backend)
        return view(request, *args, **kwargs)


class AccessTokenView(_DispatchingView):
    """
    Handle access token requests.
    """
    dot_view = dot_views.TokenView
    dop_view = dop_views.AccessTokenView
