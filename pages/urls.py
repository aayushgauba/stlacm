from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/', views.calendar_events_api, name='calendar-events-api'),
    path('meetups/<int:meetup_id>/', views.meetup_detail, name='meetup-detail'),
]
