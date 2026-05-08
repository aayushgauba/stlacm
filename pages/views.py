import json
from urllib.error import URLError
from urllib.request import urlopen

from django.http import JsonResponse
from django.shortcuts import render
from .models import MeetupImage, ParticipatingMeetup

EVENTS_API_URL = "https://stlcodecal.s3.us-east-2.amazonaws.com/events_latest.json"

def home(request):
    meetup_images = MeetupImage.objects.all()
    participating_meetups = ParticipatingMeetup.objects.filter(is_active=True)
    return render(
        request,
        'pages/home.html',
        {
            'meetup_images': meetup_images,
            'participating_meetups': participating_meetups,
        },
    )


def calendar_view(request):
    return render(request, 'pages/calendar.html')


def calendar_events_api(request):
    try:
        with urlopen(EVENTS_API_URL, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return JsonResponse(payload)
    except (URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse(
            {
                "lastUpdated": None,
                "lastUpdatedPretty": None,
                "events": {},
                "error": "Unable to fetch events feed.",
            },
            status=502,
        )
