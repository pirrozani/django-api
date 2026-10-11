from django.urls import include, path
from api.views import UserViewSet, BlogViewSet, HealthView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

# SimpleRouter adds trailing-slash routes (user-list, user-detail, user-blogs, blog-list, blog-detail)
# without DefaultRouter's API root and .json suffix routes, which aren't in the contract
router = SimpleRouter()
router.register('users', UserViewSet, basename='user')
router.register('blogs', BlogViewSet, basename='blog')

urlpatterns = [
    # URL for the health check (Render, frontend wake-up)
    path('health/', HealthView.as_view(), name='health'),

    # URLs for the User and Blog viewsets
    path('', include(router.urls)),

    # URL for the schema views
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
