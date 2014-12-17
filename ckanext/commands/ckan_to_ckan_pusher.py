'''
Created on 30.10.2014

@author: mvi
'''
from ckan.lib.cli import CkanCommand
import sys

import logging
from ckanext.model.publishing import external_catalog_table
log = logging.getLogger('ckanext')


class DatasetPusherCmd(CkanCommand):
    '''Pushes datasets from one ckan to another
    
    needs set properties in provided config file:
    dataset.pusher.src.ckan.url        - source ckan from which we are harvesting datasets
    dataset.pusher.dst.ckan.url        - destination ckan to which we are pushing the datasets
    dataset.pusher.dst.ckan.api.key    - destination ckan api key needed for authentication
    
    Usage:
        
        ckan_to_ckan_pusher test
        - start test that writes source and destination ckan url that are
          set in provided config file
        
        ckan_to_ckan_pusher run
        - starts pushing datasets
    '''
    
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 5
    min_args = 0
    
    def __init__(self, name):

        super(DatasetPusherCmd, self).__init__(name)

    
    def command(self):
        self._load_config()
        
        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        
        if cmd == 'test':
            log.info('Starting [DatasetPusherCmd test]')
            conf = self._get_config()
            src_ckan_url = conf.get('odn.ic2pc.src.ckan.url')
            dst_ckan_url = conf.get('odn.ic2pc.dst.ckan.url')
            dst_ckan_api_key = conf.get('odn.ic2pc.dst.ckan.api.key')
            
            package_whitelist = conf.get('odn.ic2pc.package.extras.whitelist')
            resource_whitelist = conf.get('odn.ic2pc.resource.extras.whitelist')

            log.info('source ckan url:      %s' % (src_ckan_url,))
            log.info('destination ckan url: %s' % (dst_ckan_url,))
            log.info('destination api key:  %s' % (dst_ckan_api_key,))
            
            log.info('package extras whitelist:  {0}'.format(package_whitelist))
            log.info('resource extras whitelist: {0}'.format(resource_whitelist))
            
        elif cmd == 'run':
            log.info('Starting [DatasetPusherCmd run]')
            from ckanext.dataset_pusher.pusher import CkanToCkanPusher
            from odn_ckancommons.ckan_helper import CkanAPIWrapper
            
            conf = self._get_config()
            src_ckan_url = conf.get('odn.ic2pc.src.ckan.url')
            dst_ckan_url = conf.get('odn.ic2pc.dst.ckan.url')
            dst_ckan_api_key = conf.get('odn.ic2pc.dst.ckan.api.key')
            
            package_whitelist = conf.get('odn.ic2pc.package.extras.whitelist', "")
            resource_whitelist = conf.get('odn.ic2pc.resource.extras.whitelist', "")
            
            package_whitelist = package_whitelist.split(' ')
            resource_whitelist = resource_whitelist.split(' ')
            
            assert src_ckan_url
            assert dst_ckan_url
            assert dst_ckan_api_key
            
            src_ckan = CkanAPIWrapper(src_ckan_url, None)
            dst_ckan = CkanAPIWrapper(dst_ckan_url, dst_ckan_api_key)
            pusher = CkanToCkanPusher()
            pusher.push(src_ckan, dst_ckan, whitelist_package_extras=package_whitelist,
                        whitelist_resource_extras=resource_whitelist)
            log.info('End of [DatasetPusherCmd run]')
        
        elif cmd == 'initdb':
            log.info('Starting db initialization')
            if not external_catalog_table.exists():
                log.info("creating external_catalog table")
                external_catalog_table.create()
                log.info("external_catalog table created successfully")
            else:
                log.info("external_catalog table already exists")
            log.info('End of db initialization')
        
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
        super(DatasetPusherCmd, self)._load_config()