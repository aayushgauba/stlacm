"""Shared public URLs and search metadata."""
import json

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.text import Truncator


def public_url(path):
    return f"{settings.SITE_URL.rstrip('/')}/{path.lstrip('/')}"


def metadata(request):
    return {
        'canonical_url': public_url(request.path),
        'social_image': public_url(static('infonoms/arch.jpg')),
    }


def structured_json(data):
    # Keep JSON safe inside an HTML script element, including future edited copy.
    return json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003C').replace('>', '\\u003E')


def infonoms_metadata(context, talk=None):
    home_url = public_url(reverse('infonoms'))
    title = 'Infonoms 2026 | St. Louis Tech Talks & Recordings'
    description = 'Watch eight Infonoms 2026 tech talks from St. Louis. Explore the schedule, meet the speakers, and learn about AI, software development, and cloud infrastructure.'
    page = {
        '@type': 'CollectionPage',
        'name': title,
        'url': home_url,
        'mainEntity': {
            '@type': 'ItemList',
            'itemListElement': [
                {'@type': 'ListItem', 'position': index, 'name': item['title'],
                 'url': public_url(reverse('infonoms-speaker', args=[item['speaker_slug']]))}
                for index, item in enumerate(context['talks'], start=1)
            ],
        },
    }
    graph = [page]
    if talk:
        url = public_url(reverse('infonoms-speaker', args=[talk['speaker_slug']]))
        title = f"{talk['speaker']} — {talk['title']} | Infonoms 2026"
        description = Truncator(f"{talk['speaker']} at Infonoms 2026: {talk['description']}").chars(160)
        person = {'@type': 'Person', 'name': talk['speaker'], 'description': talk['bio']}
        session = {'@type': 'CreativeWork', 'name': talk['title'], 'description': talk['description'],
                   'url': url, 'creator': person}
        if talk.get('video_id'):
            session['associatedMedia'] = {
                '@type': 'MediaObject',
                'contentUrl': f"https://www.youtube.com/watch?v={talk['video_id']}",
                'embedUrl': f"https://www.youtube-nocookie.com/embed/{talk['video_id']}",
            }
        graph = [
            {'@type': 'WebPage', 'name': title, 'url': url, 'mainEntity': session, 'about': person},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Infonoms 2026', 'item': home_url},
                {'@type': 'ListItem', 'position': 2, 'name': talk['speaker'], 'item': url},
            ]},
        ]
    return {'seo_title': title, 'seo_description': description,
            'structured_data': structured_json({'@context': 'https://schema.org', '@graph': graph})}
