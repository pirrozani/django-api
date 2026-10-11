from api.models import Blog
from api.serializers import BlogSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer


@extend_schema_view(
    list=extend_schema(operation_id='Get_Blogs'),
    create=extend_schema(operation_id='Create_Blog'),
    retrieve=extend_schema(operation_id='Get_Blog'),
    update=extend_schema(operation_id='Update_Blog'),
    partial_update=extend_schema(operation_id='Partial_Update_Blog'),
    destroy=extend_schema(operation_id='Delete_Blog'),
)
class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer
    renderer_classes = [JSONRenderer]
