from django.contrib import admin

from .models import MailingListSubscriber, MeetupImage, NewsItem, ParticipatingMeetup


@admin.register(MailingListSubscriber)
class MailingListSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "created_at", "source")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("source", "created_at")


admin.site.register(NewsItem)
admin.site.register(MeetupImage)
admin.site.register(ParticipatingMeetup)

