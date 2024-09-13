from mesh_simplification.utilities import triangulate_polygon, interpolate, calculate_aspect
from shapely.geometry import Polygon, Point


def vertex_removal(mesh, target_vertex_handle, point_tree, max_triangle_area, aspect_constraint):
    """ Deletes candidate vertices and re-triangulates the resulting hole. """

    # Handles of vertices surrounding target vertex
    target_vertex_vv_handles = [i for i in list(mesh.vv(target_vertex_handle)) if i is not target_vertex_handle]
    z_offset = mesh.vertex_property('z_offset', target_vertex_handle)

    # Handles of faces surrounding target vertex
    target_vertex_vf_handles = [i for i in list(mesh.vf(target_vertex_handle))]

    # Calculate the aspect of each triangle surrounding the target vertex
    aspect_constraint_test = True
    if aspect_constraint:
        aspects_before = list()
        for face_handle in target_vertex_vf_handles:
            fv = mesh.fv(face_handle)
            point_list = [mesh.point(vh) for vh in fv]
            tri_poly = Polygon(point_list)
            aspect = calculate_aspect(tri_poly)
            aspects_before.append(aspect)
        if len(set(aspects_before)) > 1:
            aspect_constraint_test = False

    # Conversion of handles to x,y for triangulation
    target_vertex_vv_xy = [[mesh.point(vh)[0], mesh.point(vh)[1]] for vh in target_vertex_vv_handles]

    # Generate a triangulation of the potential hole created from vertex removal
    hole_polygon = Polygon(target_vertex_vv_xy)
    triangulation_of_hole = triangulate_polygon(hole_polygon)

    # Vertices and triangles of retriangulation
    vertices, triangles = triangulation_of_hole['vertices'], triangulation_of_hole['triangles']

    # Look-up dictionary for x,y to vertex handle
    v_handle_lookup = dict()
    for v in vertices:
        index = target_vertex_vv_xy.index([v[0], v[1]])
        v_handle_lookup[index] = target_vertex_vv_handles[index]

    # Compare aspects before and after re-triangulation of hole
    if aspect_constraint and aspect_constraint_test:
        aspects_after = list()
        for tri in triangles:
            p1, p2, p3 = tri[0], tri[1], tri[2]
            vertex_list = [v_handle_lookup[p1], v_handle_lookup[p2], v_handle_lookup[p3]]
            point_list = [mesh.point(vh) for vh in vertex_list]
            tri_poly = Polygon(point_list)
            aspect = calculate_aspect(tri_poly)
            aspects_after.append(aspect)
        if set(aspects_before) != set(aspects_after):
            aspect_constraint_test = False

    triangle_area_test = True
    if max_triangle_area > 0:
        triangle_areas = list()
        for tri in triangles:
            p1, p2, p3 = tri[0], tri[1], tri[2]
            vertex_list = [v_handle_lookup[p1], v_handle_lookup[p2], v_handle_lookup[p3]]
            point_list = [mesh.point(vh) for vh in vertex_list]
            tri_poly = Polygon(point_list)
            triangle_areas.append(tri_poly.area)
        max_triangle = max(triangle_areas)
        if max_triangle > max_triangle_area:
            triangle_area_test = False

    if aspect_constraint_test and triangle_area_test:
        all_points_in_hole_idx = point_tree.query(hole_polygon, 'intersects')
        all_points_in_hole_geoms = point_tree.geometries.take(all_points_in_hole_idx).tolist()

        # Interpolate the z-value at the location of the vertex if the vertex is removed
        interpolation_test = False
        for i in range(len(all_points_in_hole_idx)):
            point = all_points_in_hole_geoms[i]
            point_xyz = [point.x, point.y, point.z]

            for tri in triangles:
                vh1, vh2, vh3 = v_handle_lookup[tri[0]], v_handle_lookup[tri[1]], v_handle_lookup[tri[2]]
                triangle_shape = Polygon([Point(mesh.point(vh1)), Point(mesh.point(vh2)), Point(mesh.point(vh3))])

                if point.intersects(triangle_shape):
                    interpolation_test = interpolate(triangle_shape, point_xyz, z_offset)
                    break
            if interpolation_test is False:
                break

        # If the vertex can be removed, delete it and fill resulting hole with triangles
        if interpolation_test:
            mesh.delete_vertex(target_vertex_handle, False)
            for tri in triangles:
                p1, p2, p3 = tri[0], tri[1], tri[2]
                vertex_list = [v_handle_lookup[p1], v_handle_lookup[p2], v_handle_lookup[p3]]
                mesh.add_face(vertex_list)

    return
