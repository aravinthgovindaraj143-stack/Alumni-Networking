from django.core.management.base import BaseCommand

from accounts.ml.kmeans import run_kmeans
from accounts.ml.knn import run_knn
from accounts.ml.recommendation import run_recommendation
from accounts.ml.sentiment import run_sentiment


class Command(BaseCommand):

    help = "Run all alumni machine learning algorithms"

    def handle(self, *args, **kwargs):

        self.stdout.write("")
        self.stdout.write(
            "======================================"
        )

        self.stdout.write(
            "       ALUMNI MACHINE LEARNING"
        )

        self.stdout.write(
            "======================================"
        )

        # K-MEANS
        self.stdout.write("")
        self.stdout.write(
            "Running K-Means..."
        )

        try:

            run_kmeans()

            self.stdout.write(
                self.style.SUCCESS(
                    "K-Means completed successfully."
                )
            )

        except Exception as error:

            self.stdout.write(
                self.style.ERROR(
                    f"K-Means error: {error}"
                )
            )

            return

        # KNN
        self.stdout.write("")
        self.stdout.write(
            "Running KNN..."
        )

        try:

            run_knn()

            self.stdout.write(
                self.style.SUCCESS(
                    "KNN completed successfully."
                )
            )

        except Exception as error:

            self.stdout.write(
                self.style.ERROR(
                    f"KNN error: {error}"
                )
            )

        # RECOMMENDATION
        self.stdout.write("")
        self.stdout.write(
            "Running Recommendation System..."
        )

        try:

            run_recommendation()

            self.stdout.write(
                self.style.SUCCESS(
                    "Recommendation completed successfully."
                )
            )

        except Exception as error:

            self.stdout.write(
                self.style.ERROR(
                    f"Recommendation error: {error}"
                )
            )

        # SENTIMENT
        self.stdout.write("")
        self.stdout.write(
            "Running Sentiment Analysis..."
        )

        try:

            run_sentiment()

            self.stdout.write(
                self.style.SUCCESS(
                    "Sentiment Analysis completed successfully."
                )
            )

        except Exception as error:

            self.stdout.write(
                self.style.ERROR(
                    f"Sentiment error: {error}"
                )
            )

        self.stdout.write("")
        self.stdout.write(
            "======================================"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "     ALL ML ALGORITHMS COMPLETED!"
            )
        )

        self.stdout.write(
            "K-Means + KNN + Recommendation + Sentiment"
        )

        self.stdout.write(
            "======================================"
        )