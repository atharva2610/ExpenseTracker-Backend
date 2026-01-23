from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

def today():
    return timezone.now().date()

def validate_year(value):
    if value < 2000 or value > timezone.datetime.now().year:
        raise ValidationError("Year cannot be less than 2000 or in future.")
    
def validate_date(value):
    if value and (value > timezone.datetime.now().date()):
        raise ValidationError("Date cannot be in future.")
    validate_oldest_date(value)
    
def validate_oldest_date(value):
    if value and value < date(year=2000, month=1, day=1):
        raise ValidationError("Date cannot be older than '2000-01-01'")