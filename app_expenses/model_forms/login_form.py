from django.forms import Form, EmailField, CharField
from django.core.exceptions import ValidationError

class MyLoginForm(Form):
    email = EmailField()
    password = CharField()

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email:
            raise ValidationError({"email": "Email ID is required."})
        if not password:
            raise ValidationError({"password": "Password is required."})

        return cleaned_data