from api.models import Blog, User
from api.serializers import BlogSerializer, UserSerializer, UserUpdateSerializer
from api.views.schema_responses import UNAUTHORIZED
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


@extend_schema_view(
    list=extend_schema(operation_id='Get_Users'),
    # Writes need a token, so they also document the anonymous 401
    create=extend_schema(operation_id='Create_User', responses={201: UserSerializer, 401: UNAUTHORIZED}),
    retrieve=extend_schema(operation_id='Get_User'),
    update=extend_schema(
        operation_id='Update_User',
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 401: UNAUTHORIZED},
    ),
    partial_update=extend_schema(
        operation_id='Partial_Update_User',
        request=UserUpdateSerializer,
        responses={200: UserSerializer, 401: UNAUTHORIZED},
    ),
    destroy=extend_schema(operation_id='Delete_User', responses={204: None, 401: UNAUTHORIZED}),
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    renderer_classes = [JSONRenderer]

    # PUT/PATCH use the serializer where the password is optional
    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return super().get_serializer_class()

    @extend_schema(operation_id='Get_User_Blogs', responses={200: BlogSerializer(many=True)})
    @action(detail=True, methods=['get'], serializer_class=BlogSerializer)
    # The blogs action lists a user's blogs: 404 only if the user doesn't exist
    def blogs(self, request, pk=None) -> Response:
        user = self.get_object()
        blogs = Blog.objects.filter(user=user)
        page = self.paginate_queryset(blogs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(blogs, many=True).data)
