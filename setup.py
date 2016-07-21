import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

from distutils.core import setup

setup(
    name = 'ratetransformer',
    packages = ['ratetransformer'],
    version = '1.1.0',
    description = 'Rate Transformer',
    author='aguinane',
    url='https://github.com/aguinane/RateTransformer',
    license='MIT',
    long_description="""
Rate Transformer

A package to perform cyclic transformer ratings.

"""

)
