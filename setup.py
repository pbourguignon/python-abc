from distutils.core import setup

setup(name='python-abc',
      version='0.1',
      description="A parallel implementation of the ABC sampling method",
      author="P.-Y. Bourguignon",
      author_email="pybourguignon@gmail.com",
      url="http://www.github.com/pbourguignon/python-abc",
      package_dir={ '': 'lib'},
      scripts=['bin/abc',],
      py_modules=['ABC','ABCmp'])

