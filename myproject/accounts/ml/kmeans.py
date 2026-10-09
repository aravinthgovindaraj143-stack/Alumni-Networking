import numpy as np

from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cluster import KMeans

from accounts.models import Alumni


def run_kmeans():

    alumni = list(Alumni.objects.all())

    if len(alumni) < 3:
        print("At least 3 alumni records are required.")
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

    kmeans = KMeans(
        n_clusters=3,
        random_state=42,
        n_init=10
    )

    clusters = kmeans.fit_predict(X)

    for i, alumnus in enumerate(alumni):

        alumnus.kmeans_cluster = int(
            clusters[i]
        )

        alumnus.save(
            update_fields=[
                "kmeans_cluster"
            ]
        )

    print()
    print("================================")
    print("       K-MEANS CLUSTERING")
    print("================================")

    for i, alumnus in enumerate(alumni):

        print(
            f"{alumnus.full_name} "
            f"-> Cluster {clusters[i]}"
        )

    print("--------------------------------")
    print(f"Total alumni: {len(alumni)}")
    print("Number of clusters: 3")
    print("K-Means results saved.")