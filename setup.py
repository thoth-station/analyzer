import os
from setuptools import setup


def get_install_requires():
    with open('requirements.txt', 'r') as requirements_file:
        # TODO: respect hashes in requirements.txt file
        res = requirements_file.readlines()
        return [req.split(' ', maxsplit=1)[0] for req in res if req]


def get_version():
    with open(os.path.join('thoth', 'analyzer', '__init__.py')) as f:
        content = f.readlines()

    for line in content:
        if line.startswith('__version__ ='):
            # dirty, remove trailing and leading chars
            return line.split(' = ')[1][1:-2]
    raise ValueError("No version identifier found")


setup(
    name='thoth-analyzer',
    version=get_version(),
    description='Analyzer library for project Thoht.',
    long_description='Analyzer library for project Thoht.',
    author='Fridolin Pokorny',
    author_email='fridolin@redhat.com',
    license='GPLv3+',
    packages=[
        'thoth.analyzer',
    ],
    zip_safe=False,
    install_requires=get_install_requires()
)
