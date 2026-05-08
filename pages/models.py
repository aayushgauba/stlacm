from django.db import models


class NewsItem(models.Model):
    date_published = models.DateField()
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        ordering = ['-date_published', '-id']

    def __str__(self):
        return f"{self.date_published} - {self.title}"


class MeetupImage(models.Model):
    image = models.ImageField(upload_to='meetup_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"Meetup Image {self.id}"


class ParticipatingMeetup(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    website_url = models.URLField(blank=True)
    logo_image = models.ImageField(upload_to='meetup_logos/', blank=True)
    logo_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
