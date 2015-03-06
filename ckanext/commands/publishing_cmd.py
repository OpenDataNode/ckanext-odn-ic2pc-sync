'''
Created on 30.10.2014

@author: mvi
'''
from ckan.lib.cli import CkanCommand
import sys

import logging
from ckanext.model.external_catalog import external_catalog_table,\
    migrate_to_v0_3, migrate_to_v0_4
log = logging.getLogger('ckanext')


class PublishingCmd(CkanCommand):
    '''Pushes datasets from one ckan to another
    
    needs set properties in provided config file:
    odn.ic2pc.src.ckan.url        - source ckan from which we are harvesting datasets
    odn.ic2pc.dst.ckan.url        - destination ckan to which we are pushing the datasets
    odn.ic2pc.dst.ckan.api.key    - destination ckan api key needed for authentication
    
    odn.ic2pc.package.extras.whitelist     - package extras allowed to be synchronized 
    odn.ic2pc.resource.extras.whitelist    - resource extras allowed to be synchronized
    
    The whitelist properties have a blank space as delimiter
    
    Usage:
        
        publishing_cmd test
        - start test that writes source and destination ckan url that are
          set in provided config file
        
        publishing_cmd run
        - starts pushing datasets
        
        publishing_cmd initdb
        - initializes DB tables needed for THIS extension
        
        publishing_cmd migrate_to_v0.3.0
        - updates db model from v0.2.x to v0.3.0
        
        publishing_cmd migrate_to_v0.4.0
        - updates db model from v0.3.x to v0.4
        
        publishing_cmd uninstall
        - drops tables in DB needed for THIS extension
    '''
    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 5
    min_args = 0
    
    def __init__(self, name):

        super(PublishingCmd, self).__init__(name)

    
    def command(self):
        self._load_config()
        
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        
        if cmd == 'test':
            log.info('Starting [PublishingCmd test]')
            conf = self._get_config()
            src_ckan_url = conf.get('odn.ic2pc.src.ckan.url')
            dst_ckan_url = conf.get('odn.ic2pc.dst.ckan.url')
            dst_ckan_api_key = conf.get('odn.ic2pc.dst.ckan.api.key')
            
            package_extras_whitelist = conf.get('odn.ic2pc.package.extras.whitelist')
            resource_extras_whitelist = conf.get('odn.ic2pc.resource.extras.whitelist')

            log.info('source ckan url:      %s' % (src_ckan_url,))
            log.info('destination ckan url: %s' % (dst_ckan_url,))
            log.info('destination api key:  %s' % (dst_ckan_api_key,))
            
            log.info('package extras whitelist:  {0}'.format(package_extras_whitelist))
            log.info('resource extras whitelist: {0}'.format(resource_extras_whitelist))
            
        elif cmd == 'run':
            log.info('Starting [PublishingCmd run]')
            from ckanext.publishing.ckan_sync import CkanSync
            from odn_ckancommons.ckan_helper import CkanAPIWrapper
            
            conf = self._get_config()
            src_ckan_url = conf.get('odn.ic2pc.src.ckan.url')
            dst_ckan_url = conf.get('odn.ic2pc.dst.ckan.url')
            dst_ckan_api_key = conf.get('odn.ic2pc.dst.ckan.api.key')
            
            package_extras_whitelist = conf.get('odn.ic2pc.package.extras.whitelist', "")
            resource_extras_whitelist = conf.get('odn.ic2pc.resource.extras.whitelist', "")
            
            package_extras_whitelist = package_extras_whitelist.split(' ')
            resource_extras_whitelist = resource_extras_whitelist.split(' ')
            
            assert src_ckan_url
            assert dst_ckan_url
            assert dst_ckan_api_key
            
            src_ckan = CkanAPIWrapper(src_ckan_url, None)
            dst_ckan = CkanAPIWrapper(dst_ckan_url, dst_ckan_api_key)
            pusher = CkanSync()
            pusher.push(src_ckan, dst_ckan, whitelist_package_extras=package_extras_whitelist,
                        whitelist_resource_extras=resource_extras_whitelist)
            log.info('End of [PublishingCmd run]')
        
        elif cmd == 'initdb':
            log.info('Starting db initialization')
            if not external_catalog_table.exists():
                log.info("creating external_catalog table")
                external_catalog_table.create()
                log.info("external_catalog table created successfully")
            else:
                log.info("external_catalog table already exists")
            log.info('End of db initialization')
        
        elif cmd == 'migrate_to_v0.3.0':
            log.info('Starting migration of DB to v0.3.0')
            migrate_to_v0_3()
            log.info('End of migration of DB to v0.3.0')
            
        elif cmd == 'migrate_to_v0.4':
            log.info('Starting migration of DB to v0.4.0')
            migrate_to_v0_4()
            log.info('End of migration of DB to v0.4.0')
        
        elif cmd == 'uninstall':
            log.info('Starting uninstall command')
            if external_catalog_table.exists():
                log.info("dropping external_catalog table")
                external_catalog_table.drop()
                log.info("dropped external_catalog table successfully")
            else:
                log.info("Table external_catalog doesn't exist")
            log.info('End of uninstall command')
        
            
            
    def _load_config(self):
        super(PublishingCmd, self)._load_config()