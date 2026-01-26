import uuid
from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .owned_model import OwnedModel

class Tag(OwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='tags')

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('name'), 'user', name='unique_tag_per_user'),
        ]

    def clean(self):
        super().clean()
        # validate user
        if not self.user_id:
            raise ValidationError({"user": "User does not exists."})
        # validate name
        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if not self.name.strip():
            raise ValidationError({"name": "Name cannot be blank or whitespace."})
        # validate uniqueness
        if Tag.objects.filter(user=self.user, name__iexact=self.name.strip()).exclude(pk=self.pk).exists():
            raise ValidationError({"name": f"Tag with Name: '{self.name}' already exists."})        

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name