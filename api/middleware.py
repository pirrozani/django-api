import logging

from rest_framework.throttling import BaseThrottle

logger = logging.getLogger(__name__)

MAX_LOGGED_HEADER = 200


class LogUserRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user

        if user.is_authenticated:
            username = user.username
        else:
            username = 'Anonymous'

        # Client IP as the throttles see it (NUM_PROXIES), plus the raw chain to
        # verify the hop count
        ip = BaseThrottle().get_ident(request)
        logger.info(
            'Request by %s using IP: %s (remote_addr=%s, x_forwarded_for=%s)',
            username,
            ip,
            request.META.get('REMOTE_ADDR'),
            # Client-controlled, so capped to keep log lines bounded
            request.META.get('HTTP_X_FORWARDED_FOR', '-')[:MAX_LOGGED_HEADER],
        )
        return response
