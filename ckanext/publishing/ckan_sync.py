'''
Created on 11.12.2014

@author: mvi
'''

import urllib2

import logging
from odn_ckancommons.JSON_Dataset import resource_create_update_with_upload,\
            load_from_dict, RESOURCE_FIELDS, filter_package_extras,\
    filter_resource_extras
log = logging.getLogger('ckanext')

ORGANIZATION_NAME = "comsode"

class CkanSync():
    

    def push(self, src_ckan, dst_ckan, package_ids=None,
             whitelist_package_extras=None,
             whitelist_resource_extras=None):
        '''
        pushes datasets from_ckan to to_ckan
        :param src_ckan: source ckan
        :type src_ckan: odn_ckancommons.CkanAPIWrapper
        :param dst_ckan: target ckan
        :type dst_ckan: odn_ckancommons.CkanAPIWrapper
        :param package_ids: dataset_obj ids from from_ckan to push to to_ckan, if not selected, all dataset_obj are pushed
        :type package_ids: list of strings
        :param whitelist_package_extras: whitelisted package extras
        :type whitelist_package_extras: list of strings
        :param whitelist_resource_extras: whitelisted resource extras
        :type whitelist_resource_extras: list of strings
        
        ::usage::
        src_ckan = CkanAPIWrapper('http://src_ckan.com', 'api_key')
        dst_ckan = CkanAPIWrapper('http://dst_ckan.com', 'api_key')
        CkanSync().push(src_ckan, dst_ckan)
        '''
        log.info('pushing datasets from %s to %s' % (src_ckan.url, dst_ckan.url,))
        
        if not package_ids:
            package_ids = src_ckan.get_all_package_ids()
        
        dataset_num = len(package_ids)        
        log.info('number of datasets: %d' % (dataset_num,))
    
        for i, dataset_id in enumerate(package_ids, start = 1):
            log.info('[%d / %d] processing dataset_obj with id/name (source ckan) %s' % (i, dataset_num, dataset_id,))
            package = src_ckan.get_package(dataset_id)
            if not package:
                log.error("No dataset found with id/name = {0}".format(dataset_id))
                continue
            dataset_obj = load_from_dict(package)
            
            try:
                found, dst_package_id = dst_ckan.package_search_by_name(dataset_obj)
                found_organization, organization = dst_ckan.find_organization(ORGANIZATION_NAME)

                if not found_organization:
                    result = dst_ckan.organization_create(ORGANIZATION_NAME)
                    # set comsode organization id
                    dataset_obj.owner_org.append(str(result['id']))
                else:
                    result = dst_ckan.organization_show(ORGANIZATION_NAME)
                    dataset_obj.owner_org = result['id']
                
                filter_package_extras(dataset_obj, whitelist_package_extras)
                
                if found:
                    dst_package_id = dst_ckan.package_update_data(dataset_id, dataset_obj.tojson_without_resource())['id']
                    log.info('[%d / %d] dataset_obj with id/name %s updated OK' % (i, dataset_num, dataset_id,))
                else:
                    dst_package_id = dst_ckan.package_create(dataset_obj)['id']
                    log.info('[%d / %d] dataset_obj %s created OK' % (i, dataset_num, dataset_id,))
                
                # now resources
                for resource in dataset_obj.resources:
                    if not resource['name']:
                        resource['name'] = ''

                    # filtering resource extra: its different from package extras !                     
                    filter_resource_extras(resource, whitelist_resource_extras)
                    
                    log.info('creating / updating resource: name=%s' % (resource['name'].encode('utf8'),))
                    resource_create_update_with_upload(dst_ckan, resource, dst_package_id, whitelist_resource_extras)
                    
            except urllib2.HTTPError,e:
                log.error(e)
    
    
  
