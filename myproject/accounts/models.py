from django.db import models
from django.db.models import Sum
from django.utils import timezone




class Alumni(models.Model):

    register_number = models.CharField(
        max_length=20,
        unique=True
    )

    successful_logins = models.PositiveIntegerField(default=0)

    full_name = models.CharField(
        max_length=100
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    batch = models.IntegerField(
        default=2027
    )

    company = models.CharField(
        max_length=100,
        blank=True
    )

    position = models.CharField(
        max_length=100,
        blank=True
    )

    # Alumni feedback
    feedback = models.TextField(
        null=True,
        blank=True
    )

    # K-Means result
    kmeans_cluster = models.IntegerField(
        null=True,
        blank=True
    )

    # KNN result
    knn_similar_alumni = models.TextField(
        null=True,
        blank=True
    )

    # Recommendation result
    recommended_alumni = models.TextField(
        null=True,
        blank=True
    )

    # Sentiment result
    sentiment_score = models.FloatField(
        null=True,
        blank=True
    )

    sentiment = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    location = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.full_name


class AlgorithmResult(models.Model):
    ALGORITHM_CHOICES = [
        ("kmeans", "KMeans"),
        ("knn", "KNN"),
        ("recommendation", "Recommendation"),
        ("sentiment", "Sentiment"),
    ]

    alumni = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="algorithm_results"
    )

    algorithm_name = models.CharField(
        max_length=30,
        choices=ALGORITHM_CHOICES,
        default="kmeans"
    )

    cluster = models.IntegerField(
        null=True,
        blank=True
    )

    similar_alumni = models.TextField(
        blank=True,
        default=""
    )

    recommended_alumni = models.TextField(
        blank=True,
        default=""
    )

    sentiment_score = models.FloatField(
        null=True,
        blank=True
    )

    sentiment = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Algorithm Result"
        verbose_name_plural = "Algorithm Results"

    def __str__(self):
        return f"{self.alumni.full_name} - {self.algorithm_name}"


class ChatMessage(models.Model):
    sender_id = models.PositiveIntegerField()
    recipient_id = models.PositiveIntegerField()
    message = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.id}: {self.sender_id} -> {self.recipient_id}"


class Event(models.Model):
    CATEGORY_CHOICES = [
        ("networking", "Networking"),
        ("career", "Career & Learning"),
        ("reunion", "Reunion"),
        ("community", "Community"),
        ("webinar", "Webinar"),
    ]

    title = models.CharField(max_length=180)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="community",
    )
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_online = models.BooleanField(default=False)
    location = models.CharField(max_length=220, blank=True)
    meeting_link = models.URLField(blank=True)
    capacity = models.PositiveIntegerField(default=100)
    chief_guest = models.CharField(max_length=140, blank=True)
    chief_guest_title = models.CharField(max_length=180, blank=True)
    chief_guest_bio = models.TextField(blank=True)
    featured_alumni = models.CharField(max_length=140, blank=True)
    featured_alumni_role = models.CharField(max_length=180, blank=True)
    agenda = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date", "start_time"]

    def __str__(self):
        return self.title

    @property
    def is_ended(self):
        today = timezone.localdate()
        current_time = timezone.localtime().time().replace(tzinfo=None)
        return self.event_date < today or (
            self.event_date == today and self.end_time <= current_time
        )

    @property
    def seats_available(self):
        registered_guests = self.registrations.aggregate(
            guests=Sum("guests")
        )["guests"] or 0
        registered_attendees = self.registrations.count() + registered_guests
        return max(self.capacity - registered_attendees, 0)


class EventRegistration(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    full_name = models.CharField(max_length=120)
    register_number = models.CharField(max_length=30)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    attendance = models.CharField(max_length=20)
    guests = models.PositiveIntegerField(default=0)
    food_preference = models.CharField(max_length=30, blank=True)
    special_requirements = models.CharField(max_length=300, blank=True)
    lunch_required = models.CharField(max_length=10, default="No")
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "register_number"],
                name="unique_event_registration",
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.event.title}"

class Job(models.Model):

    CATEGORY_CHOICES = [
        ("IT", "IT & Software"),
        ("DATA", "Data & Analytics"),
        ("AI", "AI & Machine Learning"),
        ("WEB", "Web Development"),
        ("CLOUD", "Cloud & DevOps"),
        ("INTERNSHIP", "Internship"),
        ("OTHER", "Other"),
    ]

    EXPERIENCE_CHOICES = [
        ("Fresher", "Fresher"),
        ("0-1 Years", "0-1 Years"),
        ("1-2 Years", "1-2 Years"),
        ("2-3 Years", "2-3 Years"),
        ("3+ Years", "3+ Years"),
    ]

    title = models.CharField(
        max_length=200
    )

    company = models.CharField(
        max_length=150
    )

    location = models.CharField(
        max_length=150
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default="IT"
    )

    experience = models.CharField(
        max_length=50,
        choices=EXPERIENCE_CHOICES,
        default="Fresher"
    )

    description = models.TextField()

    skills = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    job_type = models.CharField(
        max_length=50,
        default="Full Time"
    )

    company_website = models.URLField(
        blank=True,
        null=True
    )

    # IMPORTANT:
    # This must contain the official application URL
    # for this particular job.
    apply_url = models.URLField()

    posted_date = models.DateField(
        auto_now_add=True
    )

    last_date = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.title} - {self.company}"