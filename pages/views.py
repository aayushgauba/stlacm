from django.shortcuts import render
from .models import MeetupImage, ParticipatingMeetup

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
