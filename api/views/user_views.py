from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from api.models import Blog, User
from api.permissions import IsAuthorAccountOrReadOnly, IsStaff
from api.serializers import BlogSerializer, UserSerializer, UserUpdateSerializer
from api.views.schema_responses import FORBIDDEN, UNAUTHORIZED

# Writes need a token (401) and the author's own account, or staff for create/delete (403)
WRITE_ERRORS = {401: UNAUTHORIZED, 403: FORBIDDEN}


@extend_schema_view(
    list=extend_schema(operation_id='Get_Users'),
    create=extend_schema(
        operation_id='Create_User',
        responses={201: UserSerializer, **WRITE_ERRORS},
    ),
    retrieve=extend_schema(operation_id='Get_User'),
    update=extend_schema(
        operation_id='Update_User',
        request=UserUpdateSerializer,
        responses={200: UserSerializer, **WRITE_ERRORS},
    ),
    partial_update=extend_schema(
        operation_id='Partial_Update_User',
        request=UserUpdateSerializer,
        responses={200: UserSerializer, **WRITE_ERRORS},
    ),
    destroy=extend_schema(operation_id='Delete_User', responses={204: None, **WRITE_ERRORS}),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    renderer_classes = [JSONRenderer]
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorAccountOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'username', 'email']

    # POST and DELETE are staff-only on top of the usual rules
    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ('create', 'destroy'):
            permissions.append(IsStaff())
        return permissions

    # PUT/PATCH use the serializer where the password is optional
    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return super().get_serializer_class()

    @extend_schema(operation_id='Get_User_Blogs', responses={200: BlogSerializer(many=True)})
    @action(detail=True, methods=['get'], serializer_class=BlogSerializer, filter_backends=[])
    # The blogs action lists a user's blogs: 404 only if the user doesn't exist
    def blogs(self, request, pk=None) -> Response:
        user = self.get_object()
        blogs = Blog.objects.filter(user=user).select_related('user')
        page = self.paginate_queryset(blogs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(blogs, many=True).data)
