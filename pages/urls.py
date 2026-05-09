from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/', views.calendar_events_api, name='calendar-events-api'),
    path('calendar/event/', views.calendar_event_detail, name='calendar-event-detail'),
    path('meetups/<int:meetup_id>/calendar/events/', views.meetup_calendar_events_api, name='meetup-calendar-events-api'),
    path('meetups/<int:meetup_id>/', views.meetup_detail, name='meetup-detail'),
]
