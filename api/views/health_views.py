import logging

from django.db import Error, connection
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

HealthSerializer = inline_serializer(
    name='Health',
    fields={
        'status': serializers.ChoiceField(choices=['ok', 'error']),
        'db': serializers.ChoiceField(choices=['ok', 'unavailable'], required=False),
    },
)


class HealthView(APIView):
    # Public and unthrottled: Render's health check and the frontend's wake-up ping
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []
    renderer_classes = [JSONRenderer]

    @extend_schema(
        operation_id='Get_Health',
        auth=[],
        parameters=[
            OpenApiParameter(
                'db',
                OpenApiTypes.STR,
                enum=['1'],
                description='`1` also runs `SELECT 1` against the database',
            ),
        ],
        responses={200: HealthSerializer, 503: HealthSerializer},
    )
    # The get method reports that the app is up, and with ?db=1 that the database is
    def get(self, request) -> Response:
        if request.query_params.get('db') != '1':
            return Response({'status': 'ok'})
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
        # Error also covers InterfaceError, which isn't a DatabaseError
        except Error:
            logger.warning('Health check: database unavailable', exc_info=True)
            return Response(
                {'status': 'error', 'db': 'unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({'status': 'ok', 'db': 'ok'})
