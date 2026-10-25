from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.utils.html import escape

from . import views
from .models import ParticipatingMeetup
from .seo import structured_json


class StaticHomePageTests(TestCase):
    def test_home_route_resolves_to_home_view(self):
        self.assertEqual(resolve(reverse('home')).func, views.home)

    def test_home_page_returns_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_core_content_and_seo_tags(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'STL ACM Chapter')
        self.assertContains(response, '<meta name="description"', html=False)
        self.assertContains(response, '<link rel="canonical" href="https://stl.acm.org/">', html=False)
        self.assertContains(response, '<meta property="og:title"', html=False)
        self.assertContains(response, '<meta property="og:description"', html=False)
        self.assertContains(response, '<meta name="twitter:card" content="summary">', html=False)

    def test_removed_routes_return_404(self):
        for route in ['/about/', '/news/', '/venue/', '/speaking/']:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 404)


class InfonomsPageTests(TestCase):
    def test_infonoms_page_includes_published_schedule(self):
        response = self.client.get(reverse('infonoms'))
        self.assertEqual(response.status_code, 200)
        for content in [
            'Saturday, October 24',
            'Beyond RAG: Designing AI Agent Playbooks for Complex Customer Support',
            'Akshay Danthi',
            'From Zero to Cloud in 30 Minutes',
            'Lunch',
            '4:00 PM',
            'Talk recordings',
            'https://www.youtube.com/playlist?list=PLSNwhIDdWD8A',
            'Watch the talks',
            '8 talks',
            'id="venue"',
        ]:
            with self.subTest(content=content):
                self.assertContains(response, content)
        self.assertNotContains(response, 'Submit a proposal')
        self.assertNotContains(response, 'Noland')
        self.assertNotContains(response, 'Using AI for Vulnerability Analysis')
        self.assertNotContains(response, 'RSVP')
        self.assertNotContains(response, 'Latest News')
        talks = response.context['talks']
        self.assertEqual(len(talks), 8)
        for talk in talks:
            speaker_url = reverse('infonoms-speaker', args=[talk['speaker_slug']])
            self.assertContains(response, f'href="{speaker_url}"', count=3)
            self.assertContains(response, f'id="{talk["anchor"]}"')

    def test_each_speaker_page_shows_their_talk_and_bio(self):
        schedule_response = self.client.get(reverse('infonoms'))
        for talk in schedule_response.context['talks']:
            with self.subTest(speaker=talk['speaker']):
                response = self.client.get(reverse('infonoms-speaker', args=[talk['speaker_slug']]))
                self.assertEqual(response.status_code, 200)
                for content in [talk['speaker'], talk['title'], talk['description'], talk['bio']]:
                    self.assertContains(response, escape(content))
                self.assertContains(response, 'About the talk')
                self.assertContains(response, 'About the speaker')
                self.assertContains(response, f'href="/infonoms/#{talk["anchor"]}"')
                self.assertContains(response, 'Browse talk recordings')
                self.assertContains(response, talk['session'])
                self.assertNotContains(response, 'Noland')

    def test_unknown_and_removed_speakers_return_404(self):
        for slug in ['unknown-speaker', 'noland-crane']:
            with self.subTest(slug=slug):
                response = self.client.get(reverse('infonoms-speaker', args=[slug]))
                self.assertEqual(response.status_code, 404)

    def test_recordings_match_their_speakers(self):
        recordings = {
            'akshay-danthi': 'm9HJkFvHeRk',
            'kevin-lai': 'dPiNDNU-pgE',
            'garry-capps': 'HWkTTRiBxMI',
            'kyle-cunningham': 'jIwXX50PPRc',
            'michael-crist': 'vj43wVmKDo4',
            'lance-finney': 'wEsmayYvsAY',
            'ayoub-ghriss': 'Y3qlj4vTNxg',
            'asha-somayajula': 'lv8R8Ym14pU',
        }
        homepage = self.client.get(reverse('infonoms'))
        for slug, video_id in recordings.items():
            with self.subTest(speaker=slug):
                response = self.client.get(reverse('infonoms-speaker', args=[slug]))
                self.assertContains(response, f'src="https://www.youtube-nocookie.com/embed/{video_id}"', count=1)
                self.assertContains(response, f'href="https://www.youtube.com/watch?v={video_id}"')
                self.assertContains(homepage, f'href="https://www.youtube.com/watch?v={video_id}"', count=1)
                for other_id in recordings.values():
                    if other_id != video_id:
                        self.assertNotContains(response, f'/embed/{other_id}')

    @override_settings(INFONOMS_EVENT={'recordings_url': 'https://example.com/recordings'})
    def test_recordings_link_can_be_configured(self):
        response = self.client.get(reverse('infonoms'))
        self.assertContains(response, 'href="https://example.com/recordings"', count=3)
import json
import re
from xml.etree import ElementTree



@override_settings(SITE_URL='https://stl.acm.org')
class SeoTests(TestCase):
    def test_canonical_urls_strip_tracking_parameters(self):
        for path in ['/', '/infonoms/', '/infonoms/speakers/asha-somayajula/']:
            with self.subTest(path=path):
                response = self.client.get(path, {'utm_source': 'shared'})
                self.assertContains(response, f'<link rel="canonical" href="https://stl.acm.org{path}">', count=1)
                self.assertContains(response, f'<meta property="og:url" content="https://stl.acm.org{path}">')
                self.assertNotContains(response, 'utm_source')

    def test_infonoms_pages_have_unique_metadata_and_valid_structured_data(self):
        paths = [reverse('infonoms')] + [
            reverse('infonoms-speaker', args=[talk['speaker_slug']])
            for talk in views._get_infonoms_context()['talks']
        ]
        titles = set()
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                html = response.content.decode()
                title = re.search(r'<title>(.*?)</title>', html).group(1)
                self.assertNotIn(title, titles)
                titles.add(title)
                self.assertContains(response, f'<meta property="og:title" content="{title}">')
                self.assertContains(response, '<meta name="twitter:card" content="summary_large_image">')
                self.assertContains(response, 'content="https://stl.acm.org/static/infonoms/arch.jpg"')
                schema = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
                self.assertEqual(schema['@context'], 'https://schema.org')
                self.assertEqual(schema['@graph'][0]['url'], f'https://stl.acm.org{path}')
                if 'speakers' in path:
                    talk = response.context['talk']
                    session = schema['@graph'][0]['mainEntity']
                    self.assertEqual(session['creator']['name'], talk['speaker'])
                    self.assertTrue(session['associatedMedia']['embedUrl'].endswith(talk['video_id']))
                else:
                    self.assertEqual(len(schema['@graph'][0]['mainEntity']['itemListElement']), 8)

    def test_sitemap_lists_public_pages_and_active_meetups(self):
        active = ParticipatingMeetup.objects.create(name='Active', description='Community')
        inactive = ParticipatingMeetup.objects.create(name='Inactive', description='Community', is_active=False)
        response = self.client.get(reverse('sitemap'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        root = ElementTree.fromstring(response.content)
        urls = [element.text for element in root.findall('{*}url/{*}loc')]
        for talk in views._get_infonoms_context()['talks']:
            self.assertIn('https://stl.acm.org' + reverse('infonoms-speaker', args=[talk['speaker_slug']]), urls)
        self.assertIn(f'https://stl.acm.org/meetups/{active.id}/', urls)
        self.assertNotIn(f'https://stl.acm.org/meetups/{inactive.id}/', urls)
        self.assertFalse(any('/admin/' in url or '/events/' in url or 'noland' in url for url in urls))
        robots = self.client.get(reverse('robots'))
        self.assertContains(robots, 'Sitemap: https://stl.acm.org/sitemap.xml')

    def test_structured_data_cannot_close_its_script_element(self):
        value = '</script><script>alert(1)</script>'
        encoded = structured_json({'name': value})
        self.assertNotIn('<', encoded)
        self.assertEqual(json.loads(encoded)['name'], value)
