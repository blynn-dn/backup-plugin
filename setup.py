from setuptools import find_packages, setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name='backup_plugin',
    version='1.0.0',
    description='Backup',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/blynn-dn/backup-plugin',
    author='Bryan Lynn',
    license='Apache 2.0',
    install_requires=[],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
