from os.path import join, dirname

from setuptools import setup, find_packages

deps = ['bitarray-hardbyte>=1.5.0',
        'pyyaml>=3.10']
scm_version_options = {
        'write_to': 'src/retropass/version.py',
        'fallback_version': 'UNKNOWN',
        }
classifiers = ['Development Status :: 4 - Beta',
               'Intended Audience :: Developers',
               'Natural Language :: English',
               'Operating System :: OS Independent',
               'Programming Language :: Python :: 3',
               'Topic :: Software Development :: Libraries :: Python Modules']


def read(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()

setup(name='retropass',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      install_requires=deps,
      # FIXME: Pretty sure this installs scm outside pip. Maybe better to
      # encase setup in a try block and print an error suggesting it be
      # installed.
      setup_requires=['setuptools-scm>=3.3.0'],
      use_scm_version=scm_version_options,
      tests_require=['tox'],
      author='Andrew Vant',
      author_email='ajvant@gmail.com',
      classifiers=classifiers,
      description='Library and tool for generating progress passwords for old games',
      long_description=read('README.md'),
      long_description_content_type='text/markdown',
      zip_safe=False,
      keywords="rom roms nes",
      url="https://pypi.org/project/retropass/",
      test_suite='tests',
      entry_points={"console_scripts": ["retropass = retropass.cli:main"]},
      )
