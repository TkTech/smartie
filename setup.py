import os.path

from setuptools import setup, find_packages


root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')


setup(
    name='smartie',
    packages=find_packages(),
    version='1.0.3',
    description='Pure-python S.M.A.R.T library.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='https://github.com/TkTech/smartie',
    project_urls={
        'Bug Tracker': 'https://github.com/TkTech/smartie/issues'
    },
    keywords=['sensors', 'hardware', 'monitor'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-mock'
        ],
        'release': [
            'sphinx',
            'bump2version'
        ]
    }
)
