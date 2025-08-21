from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'blood_type', 'medical_conditions', 'allergies', 'medications',
            'preferred_language', 'notification_preferences'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    profile = UserProfileSerializer(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone', 'role', 'role_display',
            'is_active', 'home_address', 'emergency_contact', 'emergency_contact_phone',
            'created_at', 'updated_at', 'profile'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'phone', 'role', 'password', 'password_confirm',
            'home_address', 'emergency_contact', 'emergency_contact_phone'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create default profile
        UserProfile.objects.create(user=user)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone', 'home_address', 'emergency_contact', 'emergency_contact_phone'
        ]


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value
