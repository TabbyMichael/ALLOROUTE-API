import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestIdempotency:
    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("trip-optimize")
        self.user = User.objects.create_user(username="testuser", password="password")
        self.client.force_authenticate(user=self.user)

    def test_idempotent_request_caches_response(self):
        # 1. First request: normal
        # Providing valid parameters to ensure 200 OK
        payload = {
            "origin": "Chicago, IL", 
            "destination": "Gary, IN",
            "max_range_miles": 500,
            "miles_per_gallon": 10
        }
        
        # NOTE: Make sure the idempotency middleware isn't interfering 
        # with the request format or missing required fields.
        response1 = self.client.post(
            self.url, 
            payload, 
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="unique-key-1"
        )
        
        # If this fails, we need to print the error response to understand why
        if response1.status_code != status.HTTP_200_OK:
            print(f"DEBUG: Response 1 failed with {response1.status_code}: {response1.data}")
            
        assert response1.status_code == status.HTTP_200_OK
        
        # 2. Second request with same key: should be cached
        response2 = self.client.post(
            self.url, 
            payload, 
            format="json",
            HTTP_X_IDEMPOTENCY_KEY="unique-key-1"
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.content == response1.content
