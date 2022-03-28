import os.path

from setuptools import setup, find_packages


root = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(root, 'README.md'), 'rb') as readme:
    long_description = readme.read().decode('utf-8')


setup(
    name='smartie',
    packages=find_packages(),
    version='0.1.0',
    description='Pure-python S.M.A.R.T library.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tyler Kennedy',
    author_email='tk@tkte.ch',
    url='https://github.com/TkTech/smartie',
    keywords=['sensors', 'hardware', 'monitor'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
    ],
    extras_require={
        'test': [
            'pytest'
        ]
    }
)
