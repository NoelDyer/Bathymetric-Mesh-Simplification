import triangle
import numpy

from shapely.strtree import STRtree
from shapely.geometry import Polygon, Point
from shapely.ops import orient
from math import ceil
from bisect import bisect_left

from mesh_simplification.logger import log


def interpolate(triangle_poly, vertex_xyz, z_offset):
    p1, p2, p3 = triangle_poly.exterior.coords[0], triangle_poly.exterior.coords[1], triangle_poly.exterior.coords[2]
    weight1_numer = ((p2[1] - p3[1]) * (vertex_xyz[0] - p3[0])) + ((p3[0] - p2[0]) * (vertex_xyz[1] - p3[1]))
    weight2_numer = ((p3[1] - p1[1]) * (vertex_xyz[0] - p3[0])) + ((p1[0] - p3[0]) * (vertex_xyz[1] - p3[1]))
    denom = ((p2[1] - p3[1]) * (p1[0] - p3[0])) + ((p3[0] - p2[0]) * (p1[1] - p3[1]))

    weight1 = weight1_numer / denom  # Division by zero is a line
    weight2 = weight2_numer / denom  # Division by zero is a line
    weight3 = 1 - weight1 - weight2

    interp_z = (p1[2] * weight1) + (p2[2] * weight2) + (p3[2] * weight3)
    actual_z = vertex_xyz[2]

    if abs(interp_z - actual_z) > z_offset:
        return False
    else:
        return True


def calculate_aspect(triangle_poly):
    def calculate_normal_vector(vertex_a, vertex_b, vertex_c):
        ab = vertex_b - vertex_a
        ac = vertex_c - vertex_a
        n = numpy.cross(ab, ac)
        return n

    def calc_aspect(n_vector):
        aspect = numpy.arctan2(n_vector[0], n_vector[1])
        aspect_d = numpy.degrees(aspect) % 360.0
        return aspect_d

    ccw_polygon = orient(triangle_poly, sign=1.0)
    p1 = numpy.array(ccw_polygon.exterior.coords[0])
    p2 = numpy.array(ccw_polygon.exterior.coords[1])
    p3 = numpy.array(ccw_polygon.exterior.coords[2])

    # Calculate normal vector
    normal_vector = calculate_normal_vector(p1, p2, p3)

    # Calculate terrain aspect
    aspect_degrees = calc_aspect(normal_vector)

    # Compass direction
    compass_direction = get_compass_direction(aspect_degrees)

    return compass_direction


def get_compass_direction(input_degrees):
    orientation_degrees = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, 360]
    compass_direction = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
    idx = bisect_left(orientation_degrees, input_degrees)
    return compass_direction[idx]


def calculate_average_depth(mesh, negative_down):
    total_depth, total_points = 0, 0
    for vertex_handle in mesh.vertices():
        point = mesh.point(vertex_handle)
        point_z = point[2]
        if negative_down:
            if point_z < 0:
                total_depth += point_z
                total_points += 1
        else:
            if point_z > 0:
                total_depth += point_z
                total_points += 1

    average_depth = total_depth / total_points

    return average_depth


def triangulate_polygon(polygon):
    """ Uses a Python wrapper of Triangle (Shechuck, 1996) to triangulate a set of points."""

    x, y = polygon.exterior.coords.xy
    del x[-1], y[-1]
    points = numpy.stack((x, y), axis=1)

    # Constrained
    # p: PSLG; C: Exact arithmetic; S_: Steiner point limit; i: Incremental triangulation algorithm
    triangulation = triangle.triangulate({'vertices': points,
                                          'segments': create_idx(0, len(x)-1)},
                                         'pCS0i')
                                 
    return triangulation


def create_idx(start, end):
    """ Creates indexes for vertices so that segments can be created for a constrained triangulation. """

    return [[i, i + 1] for i in range(start, end)] + [[end, start]]


def get_face_ccw(mesh, vh_list):
    point1 = mesh.point(vh_list[0])
    point2 = mesh.point(vh_list[1])
    point3 = mesh.point(vh_list[2])

    area = (point2[0]-point1[0])*(point3[1]-point1[1]) - (point3[0]-point1[0])*(point2[1]-point1[1])

    if area > 0:
        return vh_list
    elif area < 0:
        reversed_list = list(reversed(vh_list))
        return reversed_list
    else:
        log.info(str([mesh.point(vh) for vh in vh_list]) + ' is collinear')


def validate_mesh(generalized_mesh, input_points):
    generalized_face_handles = list(generalized_mesh.faces())
    fv = [list(generalized_mesh.fv(face_handle)) for face_handle in generalized_face_handles]
    generalized_triangles = numpy.array([Polygon([generalized_mesh.point(v[0]), generalized_mesh.point(v[1]), generalized_mesh.point(v[2])]) for v in fv])

    triangle_tree = STRtree(generalized_triangles, int(ceil(len(generalized_triangles) * 0.004)))

    np_point_array = numpy.array([Point(p[0]) for p in input_points])
    np_uncertainty_array = numpy.array([p[1] for p in input_points])
    violation_list = list()

    idx = 0
    for point in np_point_array:
        query_triangle_idx = triangle_tree.query(point)
        query_triangle_geom = triangle_tree.geometries.take(query_triangle_idx).tolist()
        triangle_intersect = [tri for tri in query_triangle_geom if tri.intersects(point)][0]
        point_xyz = [point.x, point.y, point.z]
        point_u = np_uncertainty_array[idx]
        if not interpolate(triangle_intersect, point_xyz, point_u):
            violation_list.append(point)

        idx += 1

    return violation_list
