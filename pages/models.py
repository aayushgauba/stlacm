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
    calendar_group_name = models.CharField(max_length=200, blank=True)
    logo_image = models.ImageField(upload_to='meetup_logos/', blank=True)
    logo_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class MailingListSubscriber(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80, blank=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.email


class MailingListCampaign(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SCHEDULED = "scheduled"
    STATUS_SENT = "sent"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_SENT, "Sent"),
    ]

    subject = models.CharField(max_length=180)
    body_text = models.TextField(help_text="Plain-text body.")
    body_html = models.TextField(blank=True, help_text="Optional HTML body.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.subject}"


class MailingListDelivery(models.Model):
    campaign = models.ForeignKey(
        MailingListCampaign, on_delete=models.CASCADE, related_name="deliveries"
    )
    subscriber = models.ForeignKey(
        MailingListSubscriber, on_delete=models.CASCADE, related_name="deliveries"
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        unique_together = [("campaign", "subscriber")]
        ordering = ["-id"]

    def __str__(self):
        return f"{self.campaign_id}->{self.subscriber.email}"
