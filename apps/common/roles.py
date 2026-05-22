from enum import Enum


class UserRole(Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ADMIN = "admin"

    @classmethod
    def choices(cls):
        return [(key.value, key.name.title()) for key in cls]


# Permission constants
PERM_VIEW_DASHBOARD = "view_dashboard"
PERM_OPTIMIZE_TRIP = "optimize_trip"
PERM_UNLIMITED_DISTANCE = "unlimited_distance"
PERM_ADVANCED_METRICS = "advanced_metrics"
PERM_MANAGE_STATIONS = "manage_stations"

# Role to Permission mapping
ROLE_PERMISSIONS = {
    UserRole.BASIC: {
        PERM_VIEW_DASHBOARD,
        PERM_OPTIMIZE_TRIP,
    },
    UserRole.PREMIUM: {
        PERM_VIEW_DASHBOARD,
        PERM_OPTIMIZE_TRIP,
        PERM_UNLIMITED_DISTANCE,
        PERM_ADVANCED_METRICS,
    },
    UserRole.ADMIN: {
        PERM_VIEW_DASHBOARD,
        PERM_OPTIMIZE_TRIP,
        PERM_UNLIMITED_DISTANCE,
        PERM_ADVANCED_METRICS,
        PERM_MANAGE_STATIONS,
    },
}
