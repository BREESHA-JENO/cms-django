from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.contrib.auth import authenticate
from .models import User
from rest_framework.permissions import AllowAny

@api_view(["POST"])
@permission_classes([AllowAny]) 
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    user = User.objects.filter(username=username).first()
    if not user:
        return Response({"error": "Invalid credentials"}, status=400)

    # Lockout check
    if user.lock_until and timezone.now() < user.lock_until:
        remaining = (user.lock_until - timezone.now()).seconds
        return Response({"error": f"Account locked. Try again in {remaining} seconds."}, status=403)

    # Authenticate user
    user_auth = authenticate(request=request, username=username, password=password)
    if not user_auth:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 3:
            user.lock_until = timezone.now() + timedelta(seconds=30)
            user.failed_login_attempts = 0
        user.save()
        return Response({"error": "Invalid credentials"}, status=400)

    # Successful login
    user.failed_login_attempts = 0
    user.lock_until = None
    user.save()

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
        },
        "access": access_token,
        "refresh": str(refresh),
    }, status=200)
