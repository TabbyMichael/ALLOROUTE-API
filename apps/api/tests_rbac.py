import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from apps.common.roles import UserRole
from apps.api.permissions import IsAdminUser, IsPremiumUser, IsBasicUser


@pytest.mark.django_db
class TestRolePermissions:
    def setup_method(self):
        self.factory = APIRequestFactory()
        
        # Create users
        self.admin_user = User.objects.create_user(username="admin", password="pass", email="admin@test.com")
        self.admin_user.profile.role = UserRole.ADMIN.value
        self.admin_user.profile.save()
        
        self.premium_user = User.objects.create_user(username="premium", password="pass", email="premium@test.com")
        self.premium_user.profile.role = UserRole.PREMIUM.value
        self.premium_user.profile.save()
        
        self.basic_user = User.objects.create_user(username="basic", password="pass", email="basic@test.com")
        # Default is basic
        
        self.anon_user = User.objects.create_user(username="anon", password="pass") # but we won't authenticate him

    def test_is_admin_user(self):
        perm = IsAdminUser()
        
        # Admin should pass
        request = self.factory.get("/")
        request.user = self.admin_user
        assert perm.has_permission(request, None) is True
        
        # Premium should fail
        request.user = self.premium_user
        assert perm.has_permission(request, None) is False
        
        # Basic should fail
        request.user = self.basic_user
        assert perm.has_permission(request, None) is False

    def test_is_premium_user(self):
        perm = IsPremiumUser()
        
        # Admin should pass
        request = self.factory.get("/")
        request.user = self.admin_user
        assert perm.has_permission(request, None) is True
        
        # Premium should pass
        request.user = self.premium_user
        assert perm.has_permission(request, None) is True
        
        # Basic should fail
        request.user = self.basic_user
        assert perm.has_permission(request, None) is False

    def test_is_basic_user(self):
        perm = IsBasicUser()
        
        # Admin should pass
        request = self.factory.get("/")
        request.user = self.admin_user
        assert perm.has_permission(request, None) is True
        
        # Basic should pass
        request.user = self.basic_user
        assert perm.has_permission(request, None) is True
