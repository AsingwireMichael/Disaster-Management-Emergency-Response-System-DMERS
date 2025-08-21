from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.UserCreateView.as_view(), name='register'),
    path('auth/login/', views.login_view, name='login'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/me/', views.current_user_view, name='current_user'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # User management endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/me/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/profile/', views.UserProfileUpdateView.as_view(), name='user_profile_update'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
]
