from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.common.roles import UserRole


class AlloRouteTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Customizes the JWT payload to include role and tier information.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Tokenization: Add custom claims
        # Try to get role from profile
        profile = getattr(user, "profile", None)
        role_value = profile.role if profile else UserRole.BASIC.value
        
        token["role"] = role_value
        token["tier"] = role_value # In this system, tier and role are currently mapped 1:1
        token["username"] = user.username

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add extra data to the response (optional, but helpful for frontend)
        profile = getattr(self.user, "profile", None)
        data["role"] = profile.role if profile else UserRole.BASIC.value
        data["username"] = self.user.username
        
        return data
