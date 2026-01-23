from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.auth_serializers import *
from app_expenses.services.auth_service.user_login_service import authenticate_by_email

class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate_by_email(email, password)
        if user is not None:
            refresh_token = RefreshToken.for_user(user)
            return Response({
                "message": "Logged-in successfully!!!",
                "payload": {
                    "user": UserSerializer(user).data,
                    "tokens": {
                        "refresh": str(refresh_token),
                        "access": str(refresh_token.access_token)
                    }
                }
            }, status=status.HTTP_200_OK)
        return Response({"message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class UserAPIView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user).data,
                "message": "User created successfully. Please log in."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

