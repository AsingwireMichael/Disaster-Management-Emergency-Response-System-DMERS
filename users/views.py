from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from .models import User, UserProfile
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    LoginSerializer, ChangePasswordSerializer, UserProfileSerializer
)


class UserCreateView(generics.CreateAPIView):
    """Create a new user account."""
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]


class UserDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve and update user information."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileUpdateView(generics.UpdateAPIView):
    """Update user profile information."""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile


class ChangePasswordView(generics.UpdateAPIView):
    """Change user password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """User login endpoint."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """User logout endpoint."""
    try:
        request.user.auth_token.delete()
    except:
        pass
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """Get current authenticated user information."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


class UserListView(generics.ListAPIView):
    """List users (admin only)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'full_name', 'phone']
    ordering_fields = ['created_at', 'full_name']
    ordering = ['-created_at']


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def toggle_user_status(request, user_id):
    """Toggle user active status (admin only)."""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    return Response({
        'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
        'user_id': user.id,
        'is_active': user.is_active
    }, status=status.HTTP_200_OK)
