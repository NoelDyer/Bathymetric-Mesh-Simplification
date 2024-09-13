from mesh_simplification.utilities import get_face_ccw


class Writer(object):

    @staticmethod
    def write_mesh_gr3(mesh, file_name):
        out_url = file_name + ".gr3"
        outfile = open(out_url, 'w')
        num_vertices = mesh.n_vertices()
        num_triangles = mesh.n_faces()

        outfile.write("hgrid.gr3\n")
        outfile.write(str(num_triangles) + " " + str(int(num_vertices)) + "\n")

        vertices_sorted_idx = sorted([v.idx() for v in mesh.vertices()])
        for v_idx in vertices_sorted_idx:
            vertex_handle = mesh.vertex_handle(v_idx)
            point = mesh.point(vertex_handle)
            idx = v_idx + 1  # indexing starts from 1 in gr3 format
            outfile.write(str(idx) + " " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + "\n")

        faces_sorted_idx = sorted([v.idx() for v in mesh.faces()])
        for f_idx in faces_sorted_idx:
            face_handle = mesh.face_handle(f_idx)
            fv = list(mesh.fv(face_handle))
            fv_ccw = get_face_ccw(mesh, fv)
            idx = f_idx + 1  # indexing starts from 1 in gr3 format
            idx1, idx2, idx3 = fv_ccw[0].idx()+1, fv_ccw[1].idx()+1, fv_ccw[2].idx()+1
            outfile.write(str(idx) + " 3 " + str(idx1) + " " + str(idx2) + " " + str(idx3) + "\n")

        outfile.close()
        return

    @staticmethod
    def write_mesh_vtk(mesh, file_name):
        out_url = file_name + ".vtk"
        outfile = open(out_url, 'w')
        num_vertices = mesh.n_vertices()
        num_triangles = mesh.n_faces()

        outfile.write("# vtk DataFile Version 2.0\n\n")
        outfile.write("ASCII\n")
        outfile.write("DATASET UNSTRUCTURED_GRID\n")
        outfile.write("POINTS " + str(num_vertices) + " float\n")

        vertices_sorted_idx = sorted([v.idx() for v in mesh.vertices()])
        for v_idx in vertices_sorted_idx:
            vertex_handle = mesh.vertex_handle(v_idx)
            point = mesh.point(vertex_handle)
            outfile.write(str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + "\n")

        outfile.write("CELLS " + str(num_triangles) + " " + str(int(num_triangles)*4) + "\n")

        faces_sorted_idx = sorted([v.idx() for v in mesh.faces()])
        for f_idx in faces_sorted_idx:
            face_handle = mesh.face_handle(f_idx)
            fv = list(mesh.fv(face_handle))
            fv_ccw = get_face_ccw(mesh, fv)
            idx1, idx2, idx3 = fv_ccw[0].idx(), fv_ccw[1].idx(), fv_ccw[2].idx()
            outfile.write(" 3 " + str(idx1) + " " + str(idx2) + " " + str(idx3) + "\n")

        outfile.write("CELL_TYPES " + str(num_triangles) + "\n")

        for i in range(num_triangles):
            outfile.write(str(6) + " ")
        outfile.write("\n")

        outfile.write("POINT_DATA " + str(num_vertices) + "\n")
        outfile.write("FIELD FieldData 1 \n\n")
        outfile.write("fieldvalue 1 " + str(num_vertices) + " float \n")

        for v_idx in vertices_sorted_idx:
            vertex_handle = mesh.vertex_handle(v_idx)
            point = mesh.point(vertex_handle)
            outfile.write(str(point[2]) + " ")
        outfile.write("\n")

        outfile.close()
        return

    @staticmethod
    def write_violations_xyz(vertex_list, file_name):
        out_url_vertices = file_name + "_xyz.txt"
        outfile_vertices = open(out_url_vertices, 'w')

        outfile_vertices.write('x,y,z' + "\n")

        for v in vertex_list:
            outfile_vertices.write(str(v.x) + "," + str(v.y) + "," + str(v.z) + "\n")
        outfile_vertices.close()
