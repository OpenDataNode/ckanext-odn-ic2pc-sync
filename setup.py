from setuptools import setup, find_packages

version = '0.5.4'

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
                        'ckanext.commands',
                        'ckanext.publishing'
                        ],
    package_data={'': [
                       'i18n/*/LC_MESSAGES/*.po',
                       'fanstatic/*.js',
                       'fanstatic/*.css',
                       'templates/*.html',
                       'templates/package/*.html',
                       'templates/publishing/*.html'
                       ]
                  },
    include_package_data=True,
    zip_safe=False,
    install_requires=['odn-ckancommons>=0.5.1'],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.html', 'ckan', None),
        ]
    }, # for babel.extract_messages, says which are source files for translating
    entry_points=\
    """
    [ckan.plugins]
    odn_ic2pc_sync=ckanext.publishing.plugin:PublishingPlugin
    [paste.paster_command]
    odn_ic2pc_sync_cmd = ckanext.commands.publishing_cmd:PublishingCmd
    """,
)