from setuptools import setup, find_packages

setup(
    name='simplemic',
    version='0.0.0',
    description='Smart streaming from microphone',
    long_description='',
    author='Oleg Popov',
    author_email='exactstat@gmail.com',
    packages=find_packages('src'),  # Use find_packages for automatic discovery
    install_requires=open('requirements.txt').readlines(),  # Read requirements from file
    classifiers=[
        # Classify your package for discoverability on PyPI:
        # https://pypi.org/classifiers/
        'Programming Language :: Python :: 3',
    ],
    license='MIT',
    keywords='microphone, recording, phrases, audio, streaming',
    platforms='any',
)
