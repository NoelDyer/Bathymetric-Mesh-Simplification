# Bathymetric Mesh Simplification #
Accurate and timely predictions from operational forecast systems are crucial for disaster response planning during extreme weather events. Many of these forecast systems utilize unstructured mesh representations to model seafloor topography and discretize the domain. The size of the bathymetric mesh can significantly impact the runtime performance of these systems. Mesh simplification is a technique used to reduce the number of elements composing a mesh while preserving desired characteristics, such as shape and topology. Reducing the overall size of the mesh can improve the performance of any subsequent simulations performed on the mesh. In this work, vertex removal and re-triangulation operations are used to simplify a bathymetric surface model. Differences in resulting vertical offset from the original mesh and a maximum triangle area constraint are used to identify candidate vertices for elimination. Identical tidal simulations are modelled on the original and each simplified mesh. Velocity direction, velocity magnitudes, and water levels are recorded at twelve sites in New York Harbor over time. It was demonstrated that the simplified mesh derived from using even the strictest parameters for the mesh simplification was able to reduce the overall mesh size by approximately 26.81%, which resulted in a 26.38% speed improvement percentage compared to the un-simplified mesh. Reduction of the overall mesh size was dependent on the parameters for simplification and the speed improvement percentage was relative to the number of resulting elements composing the simplified mesh.

### Reference Paper ###
Dyer, N., Mani, S., Moghimi, S., De Floriani, L., & Zhang, J. (In Review). Bathymetric Mesh Simplification and Modelled Coastal Ocean Tide Observations in New York Harbor. Ocean Modelling.</br>

Preprint Available at SSRN: https://ssrn.com/abstract=4932300

### Installation ###
Once in the root of the repository, enter into the command line:
```
python setup.py install  # installs to current Python environment (including required libraries)
```
You should then be able to execute the program from the command line as such:
```
# Simplifying the mesh using a static (non-changing) z-offset value and maximum triangle area constraint of 1,500 square meters
-i Original_Mesh.gr3 -b boundary_idx.txt -n False -v False -z 1 -t 1500 -a False

# Simplifying the mesh using a dynamic (node-level) z-offset value and maximum triangle area constraint of 1,500 square meters
-i Original_Mesh.gr3 -b boundary_idx.txt -n False -v False -z uncertainty_utm_nodes.grd -t 1500 -a False
```
Example data file formats can be found in the ```data``` directory.

### Parameters Description ###
```
-i <inputfile> -b <boundary_points> -n <negative_down> -v <validation> -z <z_offset> -t <max_triangle_area> -a <aspect_constraint>
```
```-i``` *Input Mesh* | **Required** | GR3 mesh file format</br>
```-b``` *Boundary Nodes* | **Required** | Indices of boundary nodes in the input mesh </br>
```-n``` *Negative Down* | **Required** | Boolean, True or False if depth measurements are negative </br>
```-v``` *Validation* | **Required** | Perform validation test on output </br>
```-z``` *Z-Offset* | **Required** | The local vertex-plane distance metric for identifying candidate vertices for elimination. Optionally, a GR3 file associated with the input mesh can be used to assign z-offset values at the node level (i.e., vertical uncertainty)</br>
```-t``` *Maximum Triangle Area* | **Required** | Limits the size of new triangles inserted into the mesh</br>
```-a``` *Aspect Constraint* | **Required** | Removes candidate vertex and associated triangles only if the surface aspect remains the same before and after simplification (experimental; not used in above references)</br>


**Notes:**
<p>A default horizontal/vertical spacing of 0.75 mm to the scale is used unless a different value is provided.</p>
An output log file is also created during execution.

### Requirements ###
+ Triangle (https://rufat.be/triangle/)
    * Python wrapper of Triangle (http://www.cs.cmu.edu/~quake/triangle.html)
+ Shapely >= 1.8.0
+ Numpy >= 1.21.5
+ 3.6 <= Python < 3.9
