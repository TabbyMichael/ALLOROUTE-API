from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.common.roles import UserRole


class UserProfile(models.Model):
    """
    Extends the standard User model with role-based information.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices(),
        default=UserRole.BASIC.value
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def permissions(self):
        from apps.common.roles import ROLE_PERMISSIONS
        return ROLE_PERMISSIONS.get(UserRole(self.role), set())

    def has_perm(self, perm_name):
        return perm_name in self.permissions


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
