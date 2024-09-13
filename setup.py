from setuptools import setup
import pathlib

cwd = pathlib.Path(__file__).parent.resolve()
long_description = (cwd / 'README.md').read_text(encoding='utf-8')

setup(name='mesh_simplification',
      version='1.0.0',
      description='Bathymetric Mesh Simplification',
      license='MIT',
      long_description=long_description,
      author='Noel Dyer',
      package_dir={'': 'src'},
      packages=['mesh_simplification'],
      install_requires=['triangle',
                        'numpy==1.21.5',
                        'shapely>=1.8.0'],
      python_requires='>=3.6, <4',
      url='https://github.com/NoelDyer/Bathymetric-Mesh-Simplification',
      long_description_content_type='text/markdown',
      zip_safe=True,
      entry_points={'console_scripts':
                     ['mesh_simplification=mesh_simplification.main:main']}
      )