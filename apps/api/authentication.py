from rest_framework_simplejwt.authentication import JWTAuthentication


class AlloRouteJWTAuthentication(JWTAuthentication):
    """
    Standard JWTAuthentication.
    Role data should be accessed from the request.auth (the validated token)
    in views or via custom permission classes.
    """
    pass
