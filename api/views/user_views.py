from api.models import User
from api.serializers import UserSerializer
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated


class UserListView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    @extend_schema(operation_id='Get_Users', responses={200: UserSerializer(many=True)})
    # The get method is used to get all users
    def get(self, request) -> Response:
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response({
            "Total": len(serializer.data),
            "Users": serializer.data
        })

    @extend_schema(operation_id='Create_User', request=UserSerializer, responses={201: UserSerializer})
    # The post method is used to create a new user
    def post(self, request) -> Response:
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"Users": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [JSONRenderer]

    @extend_schema(operation_id='Get_User', responses={200: UserSerializer})
    # The get method is used to get a single user
    def get(self, request, user_id) -> Response:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"message": "User id %d not found" % user_id}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @extend_schema(operation_id='Update_User', request=UserSerializer, responses={200: UserSerializer})
    # The put method is used to update a single user
    def put(self, request, user_id) -> Response:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"message": "User id %d not found" % user_id}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id='Delete_User', responses={204: None})
    # The delete method is used to delete a single user
    def delete(self, request, user_id) -> Response:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
