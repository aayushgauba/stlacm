from django.contrib import admin

from .models import MeetupImage, NewsItem, ParticipatingMeetup


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('date_published', 'title')
    search_fields = ('title', 'content')
    list_filter = ('date_published',)
    date_hierarchy = 'date_published'
    ordering = ('-date_published', '-id')


@admin.register(MeetupImage)
class MeetupImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'alt_text', 'created_at')
    list_editable = ('order',)
    search_fields = ('alt_text',)
    ordering = ('order', '-created_at')


@admin.register(ParticipatingMeetup)
class ParticipatingMeetupAdmin(admin.ModelAdmin):
    list_display = ('name', 'website_url', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'description', 'website_url')
    list_filter = ('is_active',)
    ordering = ('order', 'name')
