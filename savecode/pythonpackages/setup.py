"""setup utils"""

# -*- coding:utf-8 -*-

from pathlib import Path

import setuptools

here = Path(__file__).parent
readme: Path = here / 'README.md'

with readme.open('r', encoding='utf-8') as fp:
    long_description = fp.read()

setuptools.setup(
    name="commonbaby",
    version="2.2.2",
    author="commonbaby",
    author_email="commonbaby@commonbaby.com",
    url="commonbaby.com",
    description="2020.07.30\nutil tools for daily dev",
    license="GPL",
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='daily work setup tools',
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=[
        'requests>=2.18.4',
        'pytz>=2019.1',
        'pyOpenSSL>=19.0.0',
        'pycryptodome>=3.9.8',
        'crypto>=1.4.1',
    ],
    project_urls={'Source': 'https://commonbaby.commonbbay'})
