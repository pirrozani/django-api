import logging

logger = logging.getLogger(__name__)


class LogUserRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        user = request.user

        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        if user.is_authenticated:
            username = user.username
        else:
            username = 'Anonymous'
        logger.info(f"Request by {username} using IP: {ip}")
        return response
