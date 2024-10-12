from setuptools import setup, find_packages

setup(
    name='python-dot-tree',
    version='1.0.8',
    author='nebko16',
    author_email='nebko16@gmail.com',
    description='Asset manager for python that leverages dot notation for simplified usage',
    license='GPL-3.0',
    keywords='asset manager dot notation dot-notation pygame images textures sprites sounds fonts files caching loading',
    packages=find_packages(where='src'),
    install_requires=[
        'setuptools',
        'pygame-ce',
        'appdirs'
    ],
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>=3.6',
    long_description='Dot notation asset manager for python to greatly simplify and shorten code related to asset management.  Includes caching, preloading, and other helpful tools.  Also includes a PyGame-CE specific extension that further simplifies managing assets for PyGame projects.',
    long_description_content_type='text/markdown',
    url='https://github.com/nebko16/dot_tree',
)
