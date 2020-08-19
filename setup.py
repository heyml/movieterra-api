from setuptools import setup, find_packages

setup(
    name='movieterra',
    version='0.0.1',
    author='Liubava',
    author_email='chamberikjorik@gmail.com',
    packages=find_packages(),
    install_requires=[ 
        'flask',
        'flask-cors',
        'flask-sqlalchemy',
        'bs4',
        'requests',
        'PyMySQL',
        'lxml',
        'gunicorn'
    ]
)