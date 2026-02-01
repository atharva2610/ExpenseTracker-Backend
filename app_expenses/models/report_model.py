import uuid
import calendar
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from .owned_model import OwnedModel
from ..custom_validators import validate_year

class Report(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    year = models.PositiveSmallIntegerField(validators=[validate_year], db_index=True)
    month = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], db_index=True)
    total_debit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_credit = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    is_dirty = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'year', 'month'], name='unique_report_per_user_month'),
            models.CheckConstraint(condition=models.Q(month__gt=0) & models.Q(month__lte=12), name='valid_month'),
            models.CheckConstraint(condition=models.Q(total_debit__gte=0), name='postive_total_debit'),
            models.CheckConstraint(condition=models.Q(total_credit__gte=0), name='positive_total_credit'),
        ]
    
    @property
    def net_balance(self):
        return self.total_credit - self.total_debit
    
    @property
    def month_year(self):
        return f"{calendar.month_name[self.month]}, {self.year}"
    
    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate year
        if not self.year:
            raise ValidationError({"year": "Year is required."})
        # validate month
        if not self.month:
            raise ValidationError({"month": "Month is required."})
        # validate uniqueness
        if Report.objects.filter(user=self.user, year=self.year, month=self.month).exclude(pk=self.pk).exists():
            raise ValidationError({"month": f"Report with Month Year: '{self.month_year}' already exists."})

    def __str__(self):
        return f"{self.user} - {self.month_year}"