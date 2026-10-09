from django.db import models


class Alumni(models.Model):

    register_number = models.CharField(
        max_length=20,
        unique=True
    )

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