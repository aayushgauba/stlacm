import json
import re
from datetime import datetime
from urllib.error import URLError
from urllib.request import urlopen

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
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


def _fetch_events_payload():
    try:
        with urlopen(EVENTS_API_URL, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, TimeoutError, json.JSONDecodeError):
        return {
            "lastUpdated": None,
            "lastUpdatedPretty": None,
            "events": {},
            "error": "Unable to fetch events feed.",
        }


def _normalize_name(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def _events_for_meetup(events_map, meetup_name):
    if meetup_name in events_map:
        return events_map[meetup_name]

    wanted = _normalize_name(meetup_name)
    for group_name, items in events_map.items():
        if _normalize_name(group_name) == wanted:
            return items
    return []


def meetup_detail(request, meetup_id):
    meetup = get_object_or_404(ParticipatingMeetup, pk=meetup_id, is_active=True)
    payload = _fetch_events_payload()
    events_map = payload.get("events", {})
    meetup_events = _events_for_meetup(events_map, meetup.name)
    meetup_events = sorted(meetup_events, key=lambda item: item.get("start", ""))
    for event in meetup_events:
        start_raw = event.get("start", "")
        try:
            parsed = datetime.fromisoformat(start_raw)
            day = parsed.strftime("%d").lstrip("0") or "0"
            hour = parsed.strftime("%I").lstrip("0") or "0"
            event["start_pretty"] = f"{parsed.strftime('%b')} {day}, {parsed.strftime('%Y')} {hour}:{parsed.strftime('%M')} {parsed.strftime('%p')}"
        except ValueError:
            event["start_pretty"] = start_raw
    return render(
        request,
        "pages/meetup_detail.html",
        {
            "meetup": meetup,
            "meetup_events": meetup_events,
            "last_updated_pretty": payload.get("lastUpdatedPretty"),
        },
    )
