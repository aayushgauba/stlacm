from django.test import TestCase, override_settings
from django.urls import resolve, reverse
from django.utils.html import escape

from . import views


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
        self.assertContains(response, '<link rel="canonical" href="http://testserver', html=False)
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
