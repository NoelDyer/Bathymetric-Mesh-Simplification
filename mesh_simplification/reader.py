import sys
import getopt
import csv
import numpy

from openmesh import TriMesh
from mesh_simplification.logger import log


class Reader(object):

    @staticmethod
    def read_arguments():
        input_file = None
        boundary_idx_list = None
        negative_down = False
        validate = False
        z_offset = None
        max_triangle_area = 0
        aspect = False

        try:
            options, remainder = getopt.getopt(sys.argv[1:], "hi:b:nvz:t:a")
        except getopt.GetoptError:
            print(sys.argv[0], ' -i <inputfile> -b <boundary_points> -n <negative_down> -v <validation> \
                                 -z <z_offset> -t <max_triangle_area> -a <aspect_constraint>')
            sys.exit(2)
        for opt, arg in options:
            if opt == '-h':
                print(sys.argv[0], ' -i <inputfile> -b <boundary_points> -n <negative_down> -v <validation> \
                                     -z <z_offset> -t <max_triangle_area> -a <aspect_constraint>')
                sys.exit()
            elif opt in "-i":
                input_file = str(arg)  
            elif opt in "-b":
                boundary_idx_list = str(arg)
            elif opt in "-n":
                negative_down = True
            elif opt in "-v":
                validate = True
            elif opt in "-z":
                z_offset = str(arg)
            elif opt in "-t":
                max_triangle_area = float(arg)
            elif opt in "-a":
                aspect = True
        # Log input parameters
        log.info('-i {} -b {} -n {} -v {} -z {} -t {} -a {}'.format(input_file, boundary_idx_list, negative_down,
                                                                    validate, z_offset, max_triangle_area, aspect))
        
        if input_file is None:
            log.critical('Source Bathymetry Not Provided')
            sys.exit()
        if boundary_idx_list is None:
            log.info('-Boundary Points Not Provided')
            sys.exit()
        if z_offset is None:
            log.info('-Enter Z-Offset Value')
            sys.exit()
        else:
            if z_offset.replace('.', '').isnumeric():
                z_float = float(z_offset)
                if z_float <= 0:
                    log.info('-Enter Z-Offset Value Greater Than 0.0')
                else:
                    log.info('-Vertical Offset: ' + z_offset)
            else:
                log.info('-Z-Offset By Individual Node File Path: ' + z_offset)
        if validate is False:
            log.info('-No Validation will be Performed')
        if negative_down is True:
            log.info('-Depths Read as Negative Values')
        else:
            log.info('-Depths Read as Positive Values')
        if aspect is True:
            log.info('-Terrain Aspect Constraint Assessed for Vertex Removal')
        else:
            log.info('-Terrain Aspect Constraint Not Assessed for Vertex Removal')
        if max_triangle_area <= 0:
            log.info('-No Area Constraint for Triangle Size')
        else:
            log.info('-Maximum Triangle Area: ' + str(max_triangle_area))

        return input_file, boundary_idx_list, negative_down, validate, z_offset, max_triangle_area, aspect

    @staticmethod
    def read_boundary_idx(url_in):
        boundary_idx_list = list()
        with open(url_in) as infile:
            reader = csv.reader(infile)
            for idx in reader:
                boundary_idx = int(idx[0])
                boundary_idx_list.append(boundary_idx)

        return boundary_idx_list

    @staticmethod
    def boundary_idx_from_hgrid(url_in):
        boundary_list = list()
        with open(url_in) as infile:
            reader = csv.reader(infile, delimiter=' ')
            rows = list(reader)
            num_faces, num_vertices = int(rows[1][0]), int(rows[1][1])
            for i in range(num_faces+num_vertices+2, len(rows)):
                row = rows[i]
                if r'!' not in str(row):
                    boundary_list.append(int(row[0]))

        # Remove any duplicates
        boundary_idx_list = list(set(boundary_list))
        return boundary_idx_list

    @staticmethod
    def read_mesh_vertices(mesh, negative_down=False):
        points_list = list()
        for vertex_handle in mesh.vertices():
            sounding = mesh.point(vertex_handle)
            vertical_uncertainty = float(mesh.vertex_property('z_offset', vertex_handle))
            if negative_down:
                z = float(sounding[2]) * -1
            else:
                z = float(sounding[2])
            x, y = float(sounding[0]), float(sounding[1])
            points_list.append([[x, y, z], vertical_uncertainty])

        return points_list

    @staticmethod
    def read_gr3_mesh(mesh_url_in, z_offset, boundary_idx_list, negative_down):
        # If z-offset is float, then update all nodes with the same value, otherwise use provided node level offset file
        individual_node_z_offset = False
        if z_offset.replace('.', '').isnumeric():
            z_offset = float(z_offset)
        else:
            individual_node_z_offset = True
            z_offset_infile = open(z_offset)
            z_offset_reader = csv.reader(z_offset_infile, delimiter=' ')
            z_offset_rows = list(z_offset_reader)

        with open(mesh_url_in) as infile:
            reader = csv.reader(infile, delimiter=' ')
            rows = list(reader)

            # header = rows[0]
            num_faces, num_vertices = int(rows[1][0]), int(rows[1][1])

            mesh = TriMesh()
            for i in range(2, num_vertices+2):
                sounding = rows[i]
                # May need to adjust negative z values
                idx, x, y, z = float(sounding[0]), float(sounding[1]), float(sounding[2]), float(sounding[3])
                vertex_handle = mesh.add_vertex(numpy.array([x, y, z]))
                # Update vertex with z_offset
                if individual_node_z_offset:
                    z_offset_sounding = z_offset_rows[i]
                    z_offset = float(z_offset_sounding[3])
                mesh.set_vertex_property('z_offset', vertex_handle, z_offset)

                # Update vertex eligibility for simplification and catalog
                if idx in boundary_idx_list:
                    # Boundary point and land point
                    if (negative_down and z > 0) or (not negative_down and z < 0):
                        mesh.set_vertex_property('omit', vertex_handle, 1)
                    # Only boundary point
                    else:
                        mesh.set_vertex_property('omit', vertex_handle, 2)
                elif (negative_down and z > 0) or (not negative_down and z < 0):
                    # Only land point
                    mesh.set_vertex_property('omit', vertex_handle, 3)
                else:
                    # Non-boundary and non-land, eligible for simplification
                    mesh.set_vertex_property('omit', vertex_handle, 0)
            for i in range(num_vertices+2, num_vertices+num_faces+2):
                face = rows[i]
                # indexing starts from 1 in gr3 format
                idx, c, idx1, idx2, idx3 = int(face[0]), int(face[1]), int(face[2])-1, int(face[3])-1, int(face[4])-1
                point1, point2, point3 = mesh.vertex_handle(idx1), mesh.vertex_handle(idx2), mesh.vertex_handle(idx3)
                mesh.add_face(point1, point2, point3)

        if individual_node_z_offset:
            z_offset_infile.close()
        return mesh
