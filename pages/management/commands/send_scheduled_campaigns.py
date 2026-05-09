from django.core.management.base import BaseCommand
from django.utils import timezone

from pages.mailing import send_campaign
from pages.models import MailingListCampaign


class Command(BaseCommand):
    help = "Send any scheduled mailing list campaigns that are due."

    def add_arguments(self, parser):
        parser.add_argument(
            "--campaign-id",
            type=int,
            default=None,
            help="Send only this campaign id (ignores scheduled_at).",
        )

    def handle(self, *args, **options):
        campaign_id = options.get("campaign_id")
        now = timezone.now()

        if campaign_id:
            campaigns = MailingListCampaign.objects.filter(id=campaign_id).exclude(
                status=MailingListCampaign.STATUS_SENT
            )
        else:
            campaigns = MailingListCampaign.objects.filter(
                status=MailingListCampaign.STATUS_SCHEDULED,
                scheduled_at__isnull=False,
                scheduled_at__lte=now,
            ).exclude(sent_at__isnull=False)

        count = 0
        for campaign in campaigns:
            sent = send_campaign(campaign)
            count += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"Sent campaign {campaign.id} to {sent} subscriber(s)."
                )
            )

        if not count:
            self.stdout.write("No campaigns due.")

