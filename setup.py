import setuptools

setup_params = dict(
    name='chilero_pg',
    use_scm_version=True,
    namespace_packages=['chilero'],
    packages=setuptools.find_packages(),
    include_package_data=True,
    url='https://github.com/dmonroy/chilero.pg',
    author='Darwin Monroy',
    author_email='contact@darwinmonroy.com',
    description='PostgreSQL utilities for chilero',
    install_requires=[
        'aiopg',
        'chilero>=0.3.7'
    ],
    setup_requires=[
        'setuptools_scm',
    ],
)


if __name__ == '__main__':
    setuptools.setup(**setup_params)
