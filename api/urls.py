from django.urls import path
from api.views import UserListView, UserDetailView, BlogListView, BlogDetailView, UserBlogView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # URLs for the User views
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>', UserDetailView.as_view(), name='user-detail'),

    # URL for the Blog views
    path('blogs/', BlogListView.as_view(), name='blog-list'),
    path('blogs/<int:blog_id>', BlogDetailView.as_view(), name='blog-detail'),
    path('blogs/user/<int:user_id>', UserBlogView.as_view(), name='user-blogs'),

    # URL for the schema views
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
