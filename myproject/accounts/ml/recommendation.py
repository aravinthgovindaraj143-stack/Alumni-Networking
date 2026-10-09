import numpy as np

from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler
)

from sklearn.metrics.pairwise import cosine_similarity

from accounts.models import Alumni


def run_recommendation():

    alumni = list(
        Alumni.objects.all()
    )

    if len(alumni) < 2:
        print(
            "At least 2 alumni records are required."
        )
        return

    batches = np.array([
        float(alumnus.batch)
        for alumnus in alumni
    ]).reshape(-1, 1)

    companies = [
        str(alumnus.company or "Unknown")
        for alumnus in alumni
    ]

    positions = [
        str(alumnus.position or "Unknown")
        for alumnus in alumni
    ]

    clusters = np.array([
        int(alumnus.kmeans_cluster)
        if alumnus.kmeans_cluster is not None
        else 0
        for alumnus in alumni
    ]).reshape(-1, 1)

    encoder = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False
    )

    categorical_data = encoder.fit_transform(
        np.array(
            list(zip(companies, positions))
        )
    )

    scaler = StandardScaler()

    numerical_data = scaler.fit_transform(
        np.hstack(
            (
                batches,
                clusters
            )
        )
    )

    X = np.hstack(
        (
            numerical_data,
            categorical_data
        )
    )

    similarity_matrix = cosine_similarity(X)

    for i, alumnus in enumerate(alumni):

        similarity_scores = (
            similarity_matrix[i]
        )

        similar_indices = np.argsort(
            similarity_scores
        )[::-1]

        recommendations = []

        for j in similar_indices:

            if j == i:
                continue

            recommendations.append(
                alumni[j].register_number
            )

            if len(recommendations) == 5:
                break

        alumnus.recommended_alumni = (
            ", ".join(recommendations)
        )

        alumnus.save(
            update_fields=[
                "recommended_alumni"
            ]
        )

    print()
    print("================================")
    print("       RECOMMENDATION SYSTEM")
    print("================================")

    for alumnus in alumni:

        print(
            f"{alumnus.full_name} -> "
            f"{alumnus.recommended_alumni}"
        )

    print("--------------------------------")
    print(f"Total alumni: {len(alumni)}")
    print("Top recommendations: 5")
    print("Recommendation results saved.")