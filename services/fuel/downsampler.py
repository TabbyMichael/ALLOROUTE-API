import math


class RouteProcessor:
    @staticmethod
    def calculate_distance(p1, p2):
        # Haversine or simple Euclidean for polyline pruning (approx)
        return (
            math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) * 69.0
        )  # ~69 miles per degree

    @classmethod
    def downsample(cls, coordinates, threshold_miles=25.0):
        if not coordinates:
            return []

        pruned = [coordinates[0]]
        last_kept = coordinates[0]

        for i in range(1, len(coordinates)):
            if cls.calculate_distance(last_kept, coordinates[i]) >= threshold_miles:
                pruned.append(coordinates[i])
                last_kept = coordinates[i]

        if coordinates[-1] != pruned[-1]:
            pruned.append(coordinates[-1])

        return pruned
