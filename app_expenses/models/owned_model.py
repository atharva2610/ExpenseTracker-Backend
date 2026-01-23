from django.db import models
from django.core.exceptions import PermissionDenied

class OwnedModel(models.Model):
    """
    Mixin for models that are owned by a User. Provides small helpers to assert
    ownership and perform save/update/create operations that validate owner at runtime.
    """
    owner_field_name = 'user'

    class Meta:
        abstract = True

    @property
    def owner(self):
        return getattr(self, self.owner_field_name, None)

    def is_owned_by(self, user):
        return self.owner is not None and user is not None and self.owner == user
    
    def assert_owned_by(self, requested_user):
        if requested_user is None:
            raise PermissionDenied("Requested User must be provided.")
        if self.owner is None:
            raise PermissionDenied("Data is predefined and not owned.")
        if self.owner != requested_user:
            raise PermissionDenied("You are not the owner.")
        
    def _clean_string_value(self):
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, str):
                value = value.strip()
                if value == "":
                    # normalize empty strings to None if field allows blank
                    if getattr(field, "blank", False) and getattr(field, "null", False):
                        value = None
            setattr(self, field.name, value)
    
    def save_obj(self):
        self._clean_string_value()
        self.full_clean()
        self.save()
        return self

    def create_by(self, requested_user):
        if not self._state.adding: # self._state.adding == True → object is not yet saved (new instance).
            raise PermissionDenied("You cannot use this method to update data.")
        self.assert_owned_by(requested_user)
        if self.owner is None:
            setattr(self, self.owner_field_name, requested_user)
        return self.save_obj()
    
    def update_by(self, requested_user):
        if self._state.adding: # self._state.adding == False → object is already saved in DB.
            raise PermissionDenied("You cannot use this method to create data.")
        self.assert_owned_by(requested_user)
        obj = self.__class__.objects.get(pk=self.pk)
        obj_owner = getattr(obj, self.owner_field_name)
        # Only the owner can update
        if obj_owner != requested_user:
            raise PermissionDenied("No permission to perform this action.")
        return self.save_obj()
    
    def delete_by(self, requested_user):
        if self._state.adding: # self._state.adding == False → object is already saved in DB.
            raise PermissionDenied("Data does not exists.")
        self.assert_owned_by(requested_user)
        obj = self.__class__.objects.get(pk=self.pk)
        obj_owner = getattr(obj, self.owner_field_name)
        # Only the owner can delete
        if obj_owner != requested_user:
            raise PermissionDenied("No permission to perform this action.")
        return self.delete()
    
    @classmethod
    def get_for_user(cls, requested_user=None, id=None):
        if requested_user is None:
            raise PermissionDenied("Requested User must be provided.")
        if id is None:
            obj = cls.objects.filter(user=requested_user)
        else:
            obj = cls.objects.get(pk=id)
            if obj.owner is not None and obj.owner != requested_user:
                raise PermissionDenied("You are not the owner.")
        return obj