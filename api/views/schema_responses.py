from drf_spectacular.utils import OpenApiResponse, inline_serializer
from rest_framework import serializers

# Error bodies shared by the endpoints' OpenAPI responses
DetailSerializer = inline_serializer(
    name='Detail',
    fields={'detail': serializers.CharField()},
)

UNAUTHORIZED = OpenApiResponse(DetailSerializer, description='Missing or invalid token')

AUTHOR_FILTER_ERROR = OpenApiResponse(
    inline_serializer(name='AuthorFilterError', fields={'author': serializers.ListField(child=serializers.CharField())}),
    description='`author` is not an integer',
)
