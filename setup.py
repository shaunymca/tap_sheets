#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='tap-sheets',
      version='1.0.7',
      description='Singer.io tap for extracting data from the Google Sheets API',
      author='Stitch',
      url='http://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_sheets'],
      install_requires=[
          'singer-python>=5.1.1',
          'requests==2.12.4',
          'backoff==1.3.2',
          'requests_mock==1.3.0',
          'jsonschema==2.6.0',
          'httplib2==0.9.2',
          'google-api-python-client==1.6.3',
          "oauth2client==4.1.2",
          'nose',
          "ratelimiter==1.2.0"
      ],
      entry_points='''
          [console_scripts]
          tap-sheets=tap_sheets:main
      ''',
      packages=find_packages(),
      include_package_data=True,
)