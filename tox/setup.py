try:
    from setuptools import setup, find_packages, Command
except ImportError:
    from distutils.core import setup, find_packages, Command

setup(name='pyzmq-tox-test',
      version='0.0.0',
      description='Test pyzmq across multiple Pythons with tox',
      long_description='',
      author='Marc Abramowitz',
      author_email='marc@marc-abramowitz.com',
      url='http://github.com/zeromq/pyzmq',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      platforms=["any"],
      test_requires=['unittest2'],
      testsuite='unittest2.collector',
)
