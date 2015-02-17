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
        pushes datasets from_ckan to dst_ckan
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
        log.info('pushing datasets from {0} to {1}'.format(src_ckan.url, dst_ckan.url,))
        
        if not package_ids:
            package_ids = src_ckan.get_all_package_ids()
        
        dataset_num = len(package_ids)        
        log.info('number of datasets: {0}'.format(dataset_num,))
    
        for i, dataset_id in enumerate(package_ids, start = 1):
            log.info('[{0} / {1}] processing dataset_obj with id/name (source ckan) {2}'.format(i, dataset_num, dataset_id))
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
                    dataset_obj.owner_org = result['id']
                else:
                    result = dst_ckan.organization_show(ORGANIZATION_NAME)
                    dataset_obj.owner_org = result['id']
                
                filter_package_extras(dataset_obj, whitelist_package_extras)
                
                if found:
                    dst_package_id = dst_ckan.package_update_data(dataset_id, dataset_obj.tojson_without_resource())['id']
                    log.info('[{0} / {1}] dataset_obj with id/name {2} updated OK'.format(i, dataset_num, dataset_id))
                else:
                    dst_package_id = dst_ckan.package_create(dataset_obj)['id']
                    log.info('[{0} / {1}] dataset_obj {2} created OK'.format(i, dataset_num, dataset_id))
                
                # now resource_names
                resource_names = []
                for resource in dataset_obj.resources:
                    if not resource['name']:
                        resource['name'] = ''

                    log.info('creating / updating resource: name={0}'.format(resource['name'].encode('utf8')))
                    resource_create_update_with_upload(dst_ckan, resource, dst_package_id, whitelist_resource_extras)
                    resource_names.append(resource['name'])
                
                log.info('deleting resources with names not in {0}'.format(resource_names))
                # delete resource not in src_ckan
                dst_ckan.delete_resources_not_with_name_in(resource_names, dst_package_id)
                
                    
            except urllib2.HTTPError,e:
                log.error(e)
    
    
  
