#!/usr/bin/env python
import sys
from os.path import dirname, abspath

from django.conf import settings

test_settings = dict(
    DATABASE_ENGINE = 'sqlite3',
    DATABASE_NAME = '',
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sites',
        'djutils',
        'spider',
    ],
)

if not settings.configured:
    settings.configure(**test_settings)

from django.test.simple import run_tests


def runtests(*test_args):
    if not test_args:
        test_args = ['spider']
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    failures = run_tests(test_args, verbosity=1, interactive=True)
    sys.exit(failures)


if __name__ == '__main__':
    runtests(*sys.argv[1:])
