import numpy

from mesh_simplification.reader import Reader
from mesh_simplification.writer import Writer
from mesh_simplification.simplification import vertex_removal
from mesh_simplification.utilities import validate_mesh, calculate_average_depth
from mesh_simplification.logger import log

from shapely.strtree import STRtree
from shapely.geometry import Point
from math import ceil


def main():

    # Read input arguments
    input_file, boundary_idx_list, negative_down, validate, z_offset, max_triangle_area, aspect = Reader.read_arguments()

    # Read boundary points
    log.info('-Reading Boundary Node Indices')
    boundary_points = Reader.read_boundary_idx(boundary_idx_list)
    log.info('-Reading Mesh')
    input_mesh = Reader.read_gr3_mesh(input_file, z_offset, boundary_points, negative_down)
    input_points = Reader.read_mesh_vertices(input_mesh, negative_down)

    # Write initial mesh file
    log.info('-Writing Initial Mesh Files')
    Writer.write_mesh_gr3(input_mesh, 'Input_Mesh')
    Writer.write_mesh_vtk(input_mesh, 'Input_Mesh')
    
    # Simplify input mesh
    log.info('-Simplifying Mesh')
    stop, iteration_count = False, 1
    while stop is False:
        # Report iteration count
        log.info('\t-Iteration Count: ' + str(iteration_count))
        
        # Report vertex/triangle count before simplification iteration
        vertex_count_before_simplification = int(input_mesh.n_vertices())
        triangle_count_before_simplification = int(input_mesh.n_faces())
        average_depth_before_simplification = float(calculate_average_depth(input_mesh, negative_down))
        log.info('\t\t-Mesh Vertices Before Iteration: ' + str(vertex_count_before_simplification))
        log.info('\t\t-Mesh Triangles Before Iteration: ' + str(triangle_count_before_simplification))
        log.info('\t\t-Average Depth Before Iteration: ' + str(average_depth_before_simplification))
        
        # Get vertex handles of mesh nodes
        vertex_handles = input_mesh.vertices()
        
        # Sort list of vertex handles by depth
        vertices_sorted = sorted([v for v in vertex_handles], key=lambda k: input_mesh.point(k)[2])

        np_point_array = numpy.array([Point(p[0]) for p in input_points])
        point_tree = STRtree(np_point_array, int(ceil(len(np_point_array) * 0.004)))

        ignore_count = 0
        for vertex_handle in vertices_sorted:
            # Skips land and boundary nodes
            if int(input_mesh.vertex_property('omit', vertex_handle)) != 0:
                ignore_count += 1
            elif float(input_mesh.vertex_property('z_offset', vertex_handle)) > input_mesh.point(vertex_handle)[2]:
                ignore_count += 1
            else:
                vertex_removal(input_mesh, vertex_handle, point_tree, max_triangle_area, aspect)

        # Garbage collection removes deleted elements from memory
        input_mesh.garbage_collection()
        
        # Report vertex/triangle count after simplification iteration
        vertex_count_after_simplification = int(input_mesh.n_vertices())
        triangle_count_after_simplification = int(input_mesh.n_faces())
        average_depth_after_simplification = float(calculate_average_depth(input_mesh, negative_down))
        log.info('\t\t-Mesh Vertices After Iteration: ' + str(vertex_count_after_simplification))
        log.info('\t\t-Mesh Triangles After Iteration: ' + str(triangle_count_after_simplification))
        log.info('\t\t-Average Depth After Iteration: ' + str(average_depth_after_simplification))
        log.info('\t\t-Total Omitted Nodes From Simplification: ' + str(ignore_count))

        # Validate simplification
        if validate:
            log.info('\t-Validating Mesh Simplification')
            violations = validate_mesh(input_mesh, input_points)
            log.info('\t\t-Violations: ' + str(len(violations)))
            Writer.write_violations_xyz(violations, 'Violations_' + str(iteration_count))
        
        # Write output file for iteration: VTK and OBJ
        log.info('\t\t-Writing Output Files')
        file_name = 'Simplified_Mesh_Iteration_' + str(iteration_count)
        Writer.write_mesh_vtk(input_mesh, file_name)
        Writer.write_mesh_gr3(input_mesh, file_name)

        # Increase iteration count
        iteration_count += 1
        
        # Stop iterations if mesh can no longer be simplified
        if vertex_count_before_simplification == vertex_count_after_simplification:
            stop = True


if __name__ == '__main__':
    main()
