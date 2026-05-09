from django.contrib import admin, messages
from django.utils import timezone
from django import forms

from .models import (
    MailingListCampaign,
    MailingListDelivery,
    MailingListSubscriber,
    MeetupImage,
    NewsItem,
    ParticipatingMeetup,
)
from .mailing import send_campaign


class MailingListCampaignAdminForm(forms.ModelForm):
    class Meta:
        model = MailingListCampaign
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        scheduled_at = cleaned.get("scheduled_at")
        if status == MailingListCampaign.STATUS_SCHEDULED and not scheduled_at:
            self.add_error("scheduled_at", "Required when status is Scheduled.")
        return cleaned


@admin.register(MailingListSubscriber)
class MailingListSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "created_at", "source")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("source", "created_at")


@admin.register(MailingListCampaign)
class MailingListCampaignAdmin(admin.ModelAdmin):
    form = MailingListCampaignAdminForm
    list_display = ("subject", "status", "scheduled_at", "sent_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "body_text", "body_html")
    readonly_fields = ("sent_at", "created_at", "updated_at")
    actions = ("send_now",)

    def send_now(self, request, queryset):
        campaigns = list(queryset)
        if not campaigns:
            return
        try:
            for campaign in campaigns:
                if campaign.status == MailingListCampaign.STATUS_SENT:
                    continue
                send_campaign(campaign)
            self.message_user(
                request, f"Sent {len(campaigns)} campaign(s).", level=messages.SUCCESS
            )
        except Exception as exc:  # noqa: BLE001
            self.message_user(request, str(exc), level=messages.ERROR)

    send_now.short_description = "Send selected campaigns now"


@admin.register(MailingListDelivery)
class MailingListDeliveryAdmin(admin.ModelAdmin):
    list_display = ("campaign", "subscriber", "sent_at")
    list_filter = ("sent_at", "campaign")
    search_fields = ("subscriber__email", "campaign__subject", "error")
    readonly_fields = ("campaign", "subscriber", "sent_at", "error")


admin.site.register(NewsItem)
admin.site.register(MeetupImage)


@admin.register(ParticipatingMeetup)
class ParticipatingMeetupAdmin(admin.ModelAdmin):
    list_display = ("name", "calendar_group_name", "is_active", "order")
    search_fields = ("name", "calendar_group_name")
    list_filter = ("is_active",)
