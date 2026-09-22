from .models import AdminActionLog




def create_admin_action_log(admin, action, target_user=None, target_reference="", reason=""):
    """Create one audit entry for a future verification/moderation action."""
    return AdminActionLog.objects.create(
        admin=admin,
        action=action,
        target_user=target_user,
        target_reference=target_reference,
        reason=reason,
    )
