from pybuilder.core import use_plugin, init, task, Author

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin("pypi:pybuilder_nose")
name = 'psiopic2'
version = '0.0.1'
authors = [Author('Alex Dowgailenko', 'adow@psikon.com')]
url = 'https://github.com/psiopic2/psiopic2'
description = 'Psiopic2 - Simple Wikimedia-based Text Classifier'
license = 'MIT'
summary = 'Psiopic2'

default_task = ['clean', 'publish']


@init
def initialize(project):

  project.depends_on_requirements('requirements.txt')
  project.build_depends_on_requirements('dev-requirements.txt')

  project.set_property('dir_source_unittest_python', 'tests')
  project.set_property('dir_source_main_python', 'src')

  project.get_property('distutils_commands')
  project.set_property('distutils_classifiers', [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7'])


