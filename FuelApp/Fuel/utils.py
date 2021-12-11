from geopy.distance import geodesic


def get_center_coordinates(points):
    sum_lat = 0
    sum_lon = 0
    for point in points:
        sum_lat += point[0]
        sum_lon += point[1]
    center = sum_lat / len(points), sum_lon / len(points)
    return center


def get_zoom(points):
    max_dist = 0
    for point1 in points:
        for point2 in points:
            point1 = point1[0], point1[1]
            point2 = point2[0], point2[1]
            distance = round(geodesic(point1, point2).km, 2)
            if distance > max_dist:
                max_dist = distance
    if max_dist <= 100:
        return 25
    elif 100 < max_dist <= 5000:
        return 4
    else:
        return 2
