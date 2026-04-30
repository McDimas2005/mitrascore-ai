from accounts.models import UserRole


def can_access_profile(user, profile):
    if user.role in {UserRole.ADMIN, UserRole.ANALYST}:
        return True
    if profile.owner_id == user.id or profile.created_by_id == user.id or profile.assisted_by_id == user.id:
        return True
    return False


def require_role(user, roles):
    return user.is_authenticated and user.role in set(roles)
