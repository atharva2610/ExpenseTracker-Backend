from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

def user_register(username=None, email=None, password=None):
    message = None
    success = False
    try:
        user = get_user_model().objects.create_user(username=username, email=email, password=password)
        user.save()
        success = True
    except ValidationError as e:
        message = e.messages[0]
    except Exception as e:
        message = str(e)
    return (success, message)