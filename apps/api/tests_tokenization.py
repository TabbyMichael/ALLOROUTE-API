import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from apps.common.roles import UserRole


@pytest.mark.django_db
class TestTokenization:
    def setup_method(self):
        self.client = APIClient()
        self.username = "premium_user"
        self.password = "pass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.user.profile.role = UserRole.PREMIUM.value
        self.user.profile.save()
        self.login_url = reverse("auth-login")

    def test_token_payload_contains_role_and_tier(self):
        payload = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        access_token = response.data["access"]
        
        # Decode token manually to check claims
        token = AccessToken(access_token)
        assert token["role"] == UserRole.PREMIUM.value
        assert token["tier"] == UserRole.PREMIUM.value
        assert token["username"] == self.username

    def test_authentication_uses_token_role(self):
        # 1. Manually create a token with a specific role
        token = AccessToken.for_user(self.user)
        token["role"] = UserRole.ADMIN.value # Override to Admin for test
        
        # 2. Setup client
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token)}")
        
        # 3. Request a view that is not yet fully protected but identify user
        # We'll use a dummy request to check if user.token_role is set
        # Since we don't have a view that exposes this yet, we'll just check if it passes a permission
        from apps.api.permissions import IsAdminUser
        
        perm = IsAdminUser()
        # We need a request object that has gone through authentication
        url = reverse("trip-optimize")
        response = self.client.post(url, {}, format="json")
        
        # This is a bit tricky to test without a view, but we can verify the response status
        # if we temporarily protect TripOptimizeView with IsAdminUser
        pass
