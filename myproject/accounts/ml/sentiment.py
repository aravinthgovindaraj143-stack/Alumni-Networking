from vaderSentiment.vaderSentiment import (
    SentimentIntensityAnalyzer
)

from accounts.models import Alumni


def run_sentiment():

    alumni = list(
        Alumni.objects.all()
    )

    if not alumni:
        print("No alumni records found.")
        return

    analyzer = SentimentIntensityAnalyzer()

    processed = 0
    skipped = 0

    for alumnus in alumni:

        feedback = str(
            alumnus.feedback or ""
        ).strip()

        if not feedback:

            skipped += 1
            continue

        scores = analyzer.polarity_scores(
            feedback
        )

        compound_score = scores["compound"]

        if compound_score >= 0.05:

            sentiment = "Positive"

        elif compound_score <= -0.05:

            sentiment = "Negative"

        else:

            sentiment = "Neutral"

        alumnus.sentiment_score = (
            compound_score
        )

        alumnus.sentiment = sentiment

        alumnus.save(
            update_fields=[
                "sentiment_score",
                "sentiment"
            ]
        )

        processed += 1

    print()
    print("================================")
    print("       SENTIMENT ANALYSIS")
    print("================================")

    print(
        f"Total alumni: {len(alumni)}"
    )

    print(
        f"Feedback analyzed: {processed}"
    )

    print(
        f"No feedback available: {skipped}"
    )

    print("--------------------------------")

    for alumnus in alumni:

        if alumnus.feedback:

            print(
                f"{alumnus.full_name} -> "
                f"{alumnus.sentiment} "
                f"({alumnus.sentiment_score})"
            )

    print("--------------------------------")
    print("Sentiment results saved.")