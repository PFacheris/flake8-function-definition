import os
from setuptools import setup, find_packages


base_dir = os.path.dirname(__file__)

about = {}
with open(
    os.path.join(base_dir, 'flake8_function_definition', '__about__.py')
) as f:
    exec(f.read(), about)

with open(os.path.join(base_dir, 'README.rst')) as f:
    long_description = f.read()


setup(
    name=about['__title__'],
    version=about['__version__'],

    description=about['__summary__'],
    long_description=long_description,
    license=about['__license__'],
    url=about['__uri__'],
    author=about['__author__'],
    author_email=about['__email__'],

    packages=find_packages(exclude=['test', 'test.*']),
    zip_safe=False,

    install_requires=[
        'flake8'
    ],

    tests_require=[
        'pytest',
        'flake8',
        'pycodestyle',
    ],

    py_modules=['flake8_function_definition'],
    entry_points={
        'flake8.extension': [
            'FD10 = flake8_function_definition.checker:'
            'FunctionDefinitionChecker',
        ],
    },

    classifiers=[
        'Framework :: Flake8',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Operating System :: OS Independent'
    ]
)
