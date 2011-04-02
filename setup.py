import os
from setuptools import setup, find_packages

from spider import VERSION

f = open(os.path.join(os.path.dirname(__file__), 'README.rst'))
readme = f.read()
f.close()

setup(
    name='django-spider',
    version=".".join(map(str, VERSION)),
    description='a multi-threaded spider with a web interface',
    long_description=readme,
    author='Charles Leifer',
    author_email='coleifer@gmail.com',
    url='https://github.com/coleifer/django-spider',
    packages=find_packages(),
    package_data = {
        'spider': [
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
)
