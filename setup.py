from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='ckanext-odn-ic2pc-sync',
    version=version,
    description="""
    Synchronizing datasets between two ckan instances
    """,
    long_description="""
    Synchronizing datasets between two ckan instances, but does the opposite of harvester, it
    pushes dataset from the ckan instance where the plugin is installed to another
    ckan instance, which may not have the plugin installed
    """,
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Martin Virag',
    author_email='martin.virag@eea.sk',
    url='',
    license='',
    packages=find_packages(exclude=['examples', 'tests']),
    namespace_packages=['ckanext',
                        'ckanext.dataset_pusher',
                        'ckanext.dataset_pusher.commands'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['odn-ckancommons>=0.2.0-SNAPSHOT'],
    entry_points=\
    """
    [ckan.plugins]
    odn_ic2pc_sync=ckanext.dataset_pusher.plugin:DatasetPusher
    [paste.paster_command]
    odn_ic2pc_sync_cmd = ckanext.dataset_pusher.commands.ckan_to_ckan_pusher:DatasetPusherCmd
    """,
)