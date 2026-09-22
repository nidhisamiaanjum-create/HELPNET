from .models import AdminActionLog


<<<<<<< HEAD
=======


>>>>>>> 17a3ceefeeadf555b9ec9c6a57e3304a6137ed5d
def create_admin_action_log(admin, action, target_user=None, target_reference="", reason=""):
    """Create one audit entry for a future verification/moderation action."""
    return AdminActionLog.objects.create(
        admin=admin,
        action=action,
        target_user=target_user,
        target_reference=target_reference,
        reason=reason,
    )
