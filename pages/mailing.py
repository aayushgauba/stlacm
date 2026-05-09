from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import MailingListCampaign, MailingListDelivery, MailingListSubscriber


def default_from_email():
    return getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(
        settings, "EMAIL_HOST_USER", None
    )


def send_campaign(campaign: MailingListCampaign) -> int:
    """
    Sends the campaign to all subscribers that have not yet received it.
    Returns the number of successful deliveries for this run.
    """
    from_email = default_from_email()
    if not from_email:
        raise RuntimeError("Missing DEFAULT_FROM_EMAIL (or EMAIL_HOST_USER) in settings.")

    subscribers = MailingListSubscriber.objects.all()
    deliveries = []
    for subscriber in subscribers:
        delivery, _created = MailingListDelivery.objects.get_or_create(
            campaign=campaign, subscriber=subscriber
        )
        deliveries.append(delivery)

    sent_count = 0
    for delivery in deliveries:
        if delivery.sent_at:
            continue
        subscriber = delivery.subscriber
        msg = EmailMultiAlternatives(
            subject=campaign.subject,
            body=campaign.body_text,
            from_email=from_email,
            to=[subscriber.email],
        )
        if campaign.body_html:
            msg.attach_alternative(campaign.body_html, "text/html")
        try:
            msg.send(fail_silently=False)
            delivery.sent_at = timezone.now()
            delivery.error = ""
            delivery.save(update_fields=["sent_at", "error"])
            sent_count += 1
        except Exception as exc:  # noqa: BLE001
            delivery.error = str(exc)[:2000]
            delivery.save(update_fields=["error"])

    campaign.sent_at = timezone.now()
    campaign.status = MailingListCampaign.STATUS_SENT
    campaign.save(update_fields=["sent_at", "status"])
    return sent_count

