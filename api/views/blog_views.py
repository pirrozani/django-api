from api.models import Blog, User
from api.permissions import IsBlogAuthorOrReadOnly
from api.serializers import BlogSerializer
from api.views.schema_responses import AUTHOR_FILTER_ERROR, FORBIDDEN, UNAUTHORIZED
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer

# Writes need a token (401) and the blog's own author account (403)
WRITE_ERRORS = {401: UNAUTHORIZED, 403: FORBIDDEN}


@extend_schema_view(
    list=extend_schema(
        operation_id='Get_Blogs',
        parameters=[OpenApiParameter('author', OpenApiTypes.INT, description='Only blogs by this author id')],
        responses={200: BlogSerializer(many=True), 400: AUTHOR_FILTER_ERROR},
    ),
    create=extend_schema(operation_id='Create_Blog', responses={201: BlogSerializer, **WRITE_ERRORS}),
    retrieve=extend_schema(operation_id='Get_Blog'),
    update=extend_schema(operation_id='Update_Blog', responses={200: BlogSerializer, **WRITE_ERRORS}),
    partial_update=extend_schema(
        operation_id='Partial_Update_Blog', responses={200: BlogSerializer, **WRITE_ERRORS},
    ),
    destroy=extend_schema(operation_id='Delete_Blog', responses={204: None, **WRITE_ERRORS}),
)
class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.select_related('user')
    serializer_class = BlogSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly, IsBlogAuthorOrReadOnly]
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

    # An account without an author profile can't post: 403 before the body is validated
    def create(self, request, *args, **kwargs):
        try:
            self.author = request.user.author
        except User.DoesNotExist:
            raise PermissionDenied('This account has no author profile, so it cannot create blogs.')
        return super().create(request, *args, **kwargs)

    # A new blog belongs to the caller's author profile, whatever `user` the body sent
    def perform_create(self, serializer):
        serializer.save(user=self.author)
