from setuptools import setup, find_packages

setup(
  name = "Psiopic2",
  version = "0.0.1",
  packages = find_packages(),
  author = "Alex Dowgailenko",
  author_email = "adow@psikon.com",
  keywords = "machine learning",
  install_requires = [
    'requests', 
    'docopt>=0.6.0',
    'appdirs',
    'blessings',
    'PyMySQL',
    'pexpect'
  ]
)
