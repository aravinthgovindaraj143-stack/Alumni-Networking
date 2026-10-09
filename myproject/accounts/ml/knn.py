import numpy as np

from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler
)

from sklearn.neighbors import NearestNeighbors

from accounts.models import Alumni


def run_knn():

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

    batch_data = scaler.fit_transform(
        batches
    )

    X = np.hstack(
        (
            batch_data,
            categorical_data
        )
    )

    number_of_neighbors = min(
        6,
        len(alumni)
    )

    knn = NearestNeighbors(
        n_neighbors=number_of_neighbors,
        metric="euclidean"
    )

    knn.fit(X)

    distances, indices = knn.kneighbors(X)

    for i, alumnus in enumerate(alumni):

        similar_alumni = []

        for j in indices[i]:

            if j == i:
                continue

            similar_alumni.append(
                alumni[j].full_name
            )

            if len(similar_alumni) == 5:
                break

        alumnus.knn_similar_alumni = (
            ", ".join(similar_alumni)
        )

        alumnus.save(
            update_fields=[
                "knn_similar_alumni"
            ]
        )

    print()
    print("================================")
    print("       KNN SIMILARITY")
    print("================================")

    for alumnus in alumni:

        print(
            f"{alumnus.full_name} -> "
            f"{alumnus.knn_similar_alumni}"
        )

    print("--------------------------------")
    print(f"Total alumni: {len(alumni)}")
    print("Top similar alumni: 5")
    print("KNN results saved.")