from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from api.views import BlogViewSet, HealthView, LoginView, LogoutView, MeView, UserViewSet

# SimpleRouter adds trailing-slash routes (user-list, user-detail, user-blogs, blog-list, blog-detail)
# without DefaultRouter's API root and .json suffix routes, which aren't in the contract
router = SimpleRouter()
router.register('users', UserViewSet, basename='user')
router.register('blogs', BlogViewSet, basename='blog')

urlpatterns = [
    # URL for the health check (Render, frontend wake-up)
    path('health/', HealthView.as_view(), name='health'),
    # URLs for the login account: get a token, revoke it, read the account
    path('auth/token/', LoginView.as_view(), name='auth-token'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    # URLs for the User and Blog viewsets
    path('', include(router.urls)),
    # URL for the schema views
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
