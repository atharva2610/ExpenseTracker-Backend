from django.forms import Form, CharField, EmailField, ValidationError
from ..utilities import email_exists

class MyUserRegisterForm(Form):
    username = CharField()
    email = EmailField()
    password = CharField()
    confirm_password = CharField()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email_exists(email):
            raise ValidationError("Email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
 
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match")