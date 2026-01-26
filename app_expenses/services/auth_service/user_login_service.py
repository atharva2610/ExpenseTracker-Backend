from django.contrib.auth import authenticate, login, logout, get_user_model
from django.core.exceptions import ValidationError, PermissionDenied

User = get_user_model()

def authenticate_by_email(email, password):
    user = User.objects.filter(email=email).first()
    if user is not None:
        user = authenticate(username=user.username, password=password)
    return user

def user_login(request, email=None, password=None):
    message = "User not found, please enter valid credentials!"
    success = False
    user = authenticate_by_email(email, password)
    if user is not None:
        login(request, user)
        message = "Logged-in successfully!!!"
        success = True
    return (success, message)