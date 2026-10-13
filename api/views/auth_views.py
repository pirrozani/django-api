from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from api.serializers import AccountSerializer
from api.views.schema_responses import UNAUTHORIZED, DetailSerializer

TokenSerializer = inline_serializer(
    name='Token',
    fields={'token': serializers.CharField()},
)

LoginErrorSerializer = inline_serializer(
    name='LoginError',
    fields={'non_field_errors': serializers.ListField(child=serializers.CharField())},
)


# Per-IP limit on login attempts, with its own rate (settings DEFAULT_THROTTLE_RATES['login'])
class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class LoginView(ObtainAuthToken):
    # No authentication: a stale token or an admin session cookie (CSRF) must not block login
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    @extend_schema(
        operation_id='Create_Auth_Token',
        auth=[],
        request=ObtainAuthToken.serializer_class,
        responses={
            200: TokenSerializer,
            400: OpenApiResponse(LoginErrorSerializer, description='Wrong or missing credentials'),
            429: OpenApiResponse(DetailSerializer, description='Too many login attempts'),
        },
    )
    # The post method exchanges a username and password for the account's token
    def post(self, request, *args, **kwargs) -> Response:
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    # Token only: logging out means revoking the token the request was made with
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        operation_id='Delete_Auth_Token', request=None, responses={204: None, 401: UNAUTHORIZED},
    )
    # The post method deletes the request's token, so it stops working
    def post(self, request) -> Response:
        request.auth.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    @extend_schema(operation_id='Get_Auth_Me', responses={200: AccountSerializer, 401: UNAUTHORIZED})
    # The get method returns the logged-in account
    def get(self, request) -> Response:
        return Response(AccountSerializer(request.user).data)
