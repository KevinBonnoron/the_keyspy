from setuptools import find_packages, setup

setup(
    name='the_keyspy',
    packages=find_packages(include=['the_keyspy']),
    version='0.0.4',
    description='The Keys Api',
    author='Kevin Bonnoron',
    author_email='kevin.bonnoron@gmail.com',
    url='https://github.com/KevinBonnoron',
    download_url='https://github.com/KevinBonnoron/the_keyspy/archive/refs/tags/v0.0.4.tar.gz',
    license='MIT',
    install_requires=['dataclasses_json', 'requests'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==6.2.4'],
    test_suite='tests',
)
