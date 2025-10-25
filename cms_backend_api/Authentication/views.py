from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.contrib.auth import authenticate
from .models import User
from rest_framework.permissions import AllowAny
from django.db.models import Q


@api_view(["POST"])
@permission_classes([AllowAny]) 
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    # Check if user exists (by username or email)
    user = User.objects.filter(Q(username=username) | Q(email=username)).first()
    if not user:
        return Response({"error": "Invalid credentials"}, status=400)

    # ✅ NEW: Check if staff account is disabled/blocked
    try:
        from admin_api_app.models import Staff  # Import Staff model
        staff = Staff.objects.filter(user=user).first()
        if staff and not staff.is_active:
            return Response(
                {"error": "Your account has been blocked. Please contact the administrator."},
                status=status.HTTP_403_FORBIDDEN
            )
    except Exception:
        # If Staff model doesn't exist or error occurs, continue with login
        pass

    # Lockout check (account temporarily locked due to failed attempts)
    if user.lock_until and timezone.now() < user.lock_until:
        remaining = (user.lock_until - timezone.now()).seconds
        return Response(
            {"error": f"Account locked due to multiple failed attempts. Try again in {remaining} seconds."},
            status=403
        )

    # Authenticate user
    user_auth = authenticate(request=request, username=username, password=password)
    if not user_auth:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 3:
            user.lock_until = timezone.now() + timedelta(seconds=30)
            user.failed_login_attempts = 0
            user.save()
            return Response(
                {"error": "Account locked due to multiple failed attempts. Try again in 30 seconds."},
                status=403
            )
        user.save()
        return Response({"error": "Invalid credentials"}, status=400)

    # Successful login - reset failed attempts
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
