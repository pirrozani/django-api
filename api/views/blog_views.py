from api.models import Blog
from api.serializers import BlogSerializer
from api.views.schema_responses import AUTHOR_FILTER_ERROR, UNAUTHORIZED
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer


@extend_schema_view(
    list=extend_schema(
        operation_id='Get_Blogs',
        parameters=[OpenApiParameter('author', OpenApiTypes.INT, description='Only blogs by this author id')],
        responses={200: BlogSerializer(many=True), 400: AUTHOR_FILTER_ERROR},
    ),
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
    queryset = Blog.objects.select_related('user')
    serializer_class = BlogSerializer
    renderer_classes = [JSONRenderer]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title']

    # The list can be narrowed to one author with ?author=<id>; an empty value means no filter
    def get_queryset(self):
        queryset = super().get_queryset()
        author = self.request.query_params.get('author')
        if self.action == 'list' and author:
            try:
                queryset = queryset.filter(user_id=int(author))
            except ValueError:
                raise ValidationError({'author': ['A valid integer is required.']})
        return queryset
