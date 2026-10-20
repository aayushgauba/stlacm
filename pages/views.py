import json
import re
from datetime import datetime
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.cache import cache
from .forms import MailingListSubscribeForm
from .models import MailingListSubscriber, MeetupImage, ParticipatingMeetup

EVENTS_API_URL = "https://stlcodecal.s3.us-east-2.amazonaws.com/events_latest.json"

def infonoms(request):
    event = {
        'city': 'St. Louis',
        'date': 'Saturday, October 24',
        'time': '10:00am–4:00pm',
        'location': 'Oak Bend Library',
        'location_url': 'https://www.slcl.org/hours-and-locations/oak-bend-branch',
        'location_note': 'St. Louis County Library',
        'format': 'Local tech mini conference',
        'rsvp_url': 'https://www.meetup.com/st-louis-computing-chapter/events/316447937',
        **getattr(settings, 'INFONOMS_EVENT', {}),
    }
    schedule = [
        {
            'label': 'Morning',
            'time': '10:00 AM',
            'items': [
                {
                    'title': 'Beyond RAG: Designing AI Agent Playbooks for Complex Customer Support',
                    'speaker': 'Akshay Danthi',
                    'description': 'RAG can retrieve information and generate answers, but complex customer support cases often require understanding underlying problems, identifying resolution steps, and executing backend actions. This session explores multi-stage LLM analysis, actionable playbooks, agent evaluation, capability gaps, and balancing accuracy, cost, and scalability.',
                    'bio': 'Akshay Danthi is a Technical Business Analyst specializing in Generative AI, AI agents, and intelligent automation. He focuses on turning complex business problems into practical AI solutions using RAG, LLM evaluation, and workflow automation.',
                },
                {
                    'title': 'Airflow for Geospatial Pipelines',
                    'speaker': 'Kevin Lai',
                    'description': 'Geospatial processing workflows often involve computationally intensive tasks, diverse data sources, and different resource requirements. This talk explores Apache Airflow’s Kubernetes Executor, declarative dataset and processing manifests, metadata-driven workflows, and scalable Kubernetes execution.',
                    'bio': 'Kevin Lai is a Geospatial Software Engineer at Xcellent Technology Solution, serving the United States Geological Survey as a contractor.',
                },
                {
                    'title': 'Local AI Agents on Modest Hardware',
                    'speaker': 'Garry Capps',
                    'description': 'This talk explores local agentic AI, from full agent harnesses running capable 27-billion-parameter models to micro-agentic systems that accomplish useful work with remarkably little computing power. It covers practical hardware, model compression, inference runtimes, context management, privacy, cost, and what useful autonomous computing can do on modest machines.',
                    'bio': 'Garry Capps is a veteran technologist with decades of experience in software development, systems architecture, and IT leadership. He currently works in R&D at Global Wafers as an AI Software Engineer specializing in LLM-based agentic implementations.',
                },
                {
                    'title': 'Zero to Cloud in 30 minutes',
                    'speaker': 'Kyle Cunningham',
                    'description': '',
                    'bio': '',
                },
            ],
        },
        {
            'label': 'Lunch',
            'time': '12:30 PM',
            'items': [],
        },
        {
            'label': 'Afternoon',
            'time': '1:30 PM',
            'items': [
                {
                    'title': 'Backpropagation Based Systems as a Model of Human Cognition',
                    'speaker': 'Michael Crist',
                    'description': 'This presentation reviews the question: to what extent can backpropagation-based systems act as a model of human cognition? It also considers how human cognition and neuroscience can inform challenges in today’s deep-learning agents.',
                    'bio': 'Michael Crist is a Senior Systems Engineer for the Department of Defense and the lead engineer for his contracting company. He is completing a Master’s Degree in Computer Science from Georgia Tech.',
                },
                {
                    'title': 'Comparing Promises, Observables, & Signals',
                    'speaker': 'Lance Finney',
                    'description': 'Promises, observables, and signals are three approaches to asynchronous and reactive programming. This session explains their differences, limitations, complementary roles, and when to choose each one in a modern JavaScript or TypeScript application.',
                    'bio': 'After more than a decade in the Java desktop world, Lance has worked in Angular, JavaScript, and TypeScript since 2014. As an Angular Google Developer Expert, he develops Angular projects and mentors junior developers.',
                },
                {
                    'title': 'How LLMs Recall',
                    'speaker': 'Ayoub Ghriss',
                    'description': 'This talk dives into the attention mechanism and how large language models use it to retrieve information.',
                    'bio': 'Ayoub Ghriss is a postdoctoral researcher at the Multimodal Vision Research Laboratory at WashU. He recently completed a PhD from CU Boulder on representation learning and efficient machine learning.',
                },
                {
                    'title': "Lifetimes in the Wild: How Reaper's Rust Editor Backend uses 'a without fear",
                    'speaker': 'Asha Somayajula',
                    'description': 'Using Reaper, an IDE with a Rust backend, this talk walks through lifetime patterns for lexers, parsers, symbol indexes, AST outlining, coverage slicing, and zero-copy agent and API request bodies. Attendees will leave with a practical checklist for when to borrow with a lifetime, use static data, or own a String.',
                    'bio': 'Asha Somayajula is a Lead Engineer and Architect based in St. Louis. She builds platform and AI-native systems and open-source tools including kdash and Reaper, and has worked at CarNow, Mastercard, the Federal Reserve Bank, HPE/USPS, and Mercy Health.',
                },
                {
                    'title': 'Using AI for Vulnerability Analysis',
                    'speaker': 'Noland Crane',
                    'description': 'Organizations may have thousands or millions of vulnerabilities identified by security tools. This talk explores how AI agents can improve the process of turning that security data into useful work for developers.',
                    'bio': 'Noland is an AI Security Engineer at Bloomreach. He has previously worked on web application penetration testing at TechGuard and vulnerability management while interning at Daimler.',
                },
            ],
        },
        {
            'label': 'Closing',
            'time': '4:00 PM',
            'items': [],
        },
    ]
    return render(request, 'pages/infonoms.html', {
        'site': {
            'title': 'infonoms',
            'description': 'Your local tech mini conference in St. Louis.',
            'event': event,
        },
        'schedule': schedule,
    })


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
