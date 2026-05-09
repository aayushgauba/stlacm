import json
import re
from datetime import datetime
from urllib.error import URLError
from urllib.request import urlopen

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.cache import cache
from .forms import MailingListSubscribeForm
from .models import MailingListSubscriber, MeetupImage, ParticipatingMeetup

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

def _get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def subscribe(request):
    form = MailingListSubscribeForm(request.POST or None)
    created = False
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST" and form.is_valid():
        ip = _get_client_ip(request)
        rate_key = f"subscribe:ip:{ip}"
        recent = cache.get(rate_key, 0)
        if recent >= 5:
            form.add_error(None, "Too many attempts. Please try again later.")
        else:
            cache.set(rate_key, recent + 1, timeout=60 * 60)
            # Honeypot: if filled, pretend success but do nothing.
            if not form.cleaned_data.get("company"):
                email = form.cleaned_data["email"].strip().lower()
                subscriber, was_created = MailingListSubscriber.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": form.cleaned_data["first_name"].strip(),
                        "last_name": form.cleaned_data.get("last_name", "").strip(),
                        "source": request.GET.get("source", "web")[:40],
                        "ip_address": ip,
                        "user_agent": (request.META.get("HTTP_USER_AGENT") or "")[:256],
                    },
                )
                if not was_created:
                    subscriber.first_name = form.cleaned_data["first_name"].strip()
                    subscriber.last_name = form.cleaned_data.get("last_name", "").strip()
                    subscriber.save(update_fields=["first_name", "last_name"])
            created = True
            form = MailingListSubscribeForm()

    if is_ajax and request.method == "POST":
        if created:
            return JsonResponse({"ok": True})
        error = "Please check the form and try again."
        if form.errors:
            error = next(iter(form.errors.values()))[0]
        if form.non_field_errors():
            error = form.non_field_errors()[0]
        return JsonResponse({"ok": False, "error": error}, status=400)

    return render(request, "pages/subscribe.html", {"form": form, "created": created})


def calendar_view(request):
    participating_meetups = list(
        ParticipatingMeetup.objects.filter(is_active=True).values(
            "id", "name", "calendar_group_name", "website_url"
        )
    )
    return render(
        request,
        "pages/calendar.html",
        {"participating_meetups": participating_meetups},
    )


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


def meetup_calendar_events_api(request, meetup_id):
    meetup = get_object_or_404(ParticipatingMeetup, pk=meetup_id, is_active=True)
    payload = _fetch_events_payload()
    events_map = payload.get("events", {}) or {}
    feed_group = meetup.calendar_group_name or meetup.name
    meetup_events = _events_for_meetup(events_map, feed_group)
    return JsonResponse(
        {
            "lastUpdated": payload.get("lastUpdated"),
            "lastUpdatedPretty": payload.get("lastUpdatedPretty"),
            "events": {meetup.name: meetup_events},
        }
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

    for group_name, items in events_map.items():
        normalized_group = _normalize_name(group_name)
        if wanted and (wanted in normalized_group or normalized_group in wanted):
            return items
    return []


def meetup_detail(request, meetup_id):
    meetup = get_object_or_404(ParticipatingMeetup, pk=meetup_id, is_active=True)
    return render(request, "pages/meetup_calendar.html", {"meetup": meetup})
