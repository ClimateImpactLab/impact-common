from setuptools import setup, find_packages

setup(name='impactcommon',
      use_scm_version=True,
      description='Library of shared tools across the impact team.',
      url='https://github.com/ClimateImpactLab/impact-common',
      author='Impacts Team',
      packages=find_packages(),
      license='GNU v. 3',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      setup_requires=['setuptools_scm'],
      install_requires=['numpy', 'pandas', 'xarray', 'metacsv', 'openest',
                        'impactlab-tools'],
      extras_require={
            'test': ['pytest'],
      }
      )
