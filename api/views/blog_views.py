from api.models import Blog
from api.serializers import BlogSerializer
from api.views.schema_responses import UNAUTHORIZED
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer


@extend_schema_view(
    list=extend_schema(operation_id='Get_Blogs'),
    # Writes need a token, so they also document the anonymous 401
    create=extend_schema(operation_id='Create_Blog', responses={201: BlogSerializer, 401: UNAUTHORIZED}),
    retrieve=extend_schema(operation_id='Get_Blog'),
    update=extend_schema(operation_id='Update_Blog', responses={200: BlogSerializer, 401: UNAUTHORIZED}),
    partial_update=extend_schema(
        operation_id='Partial_Update_Blog', responses={200: BlogSerializer, 401: UNAUTHORIZED},
    ),
    destroy=extend_schema(operation_id='Delete_Blog', responses={204: None, 401: UNAUTHORIZED}),
)
class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    renderer_classes = [JSONRenderer]
