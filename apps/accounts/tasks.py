import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_invitation_email(self, email, company_name, token, invited_role):
    """Fired asynchronously whenever a manager invites a new teammate."""
    invite_url = f"{settings.SITE_URL}/invite/accept/{token}/"
    subject = f"You've been invited to join {company_name} on TeamFlow"
    message = (
        f"Hi,\n\n"
        f"You have been invited to join {company_name} on TeamFlow as {invited_role}.\n"
        f"Accept the invitation here: {invite_url}\n\n"
        f"If you weren't expecting this, you can ignore this email."
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception("Failed to send invitation email to %s", email)
        raise self.retry(exc=exc)
