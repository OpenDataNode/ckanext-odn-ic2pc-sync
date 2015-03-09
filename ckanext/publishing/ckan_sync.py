'''
Created on 11.12.2014

@author: mvi
'''

import urllib2

import logging
from odn_ckancommons.JSON_Dataset import resource_create_update_with_upload,\
            load_from_dict, filter_package_extras
log = logging.getLogger('ckanext')


class CkanSync():
    

    def push(self, src_ckan, dst_ckan, package_ids=None,
             whitelist_package_extras=None,
             whitelist_resource_extras=None,
             org_id_name=None):
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
        :param org_id_name: id or name of organization to make owner of the dataset
        :type org_id_name: string 
        
        ::usage::
        src_ckan = CkanAPIWrapper('http://src_ckan.com', 'api_key')
        dst_ckan = CkanAPIWrapper('http://dst_ckan.com', 'api_key')
        CkanSync().push(src_ckan, dst_ckan)
        '''
        log.debug('pushing datasets from {0} to {1}'.format(src_ckan.url, dst_ckan.url, ))

        if not package_ids:
            package_ids = src_ckan.get_all_package_ids()

        dataset_num = len(package_ids)
        log.debug('number of datasets: {0}'.format(dataset_num, ))

        errors = []
        for i, dataset_id in enumerate(package_ids, start=1):
            log.debug('[{0} / {1}] processing dataset_obj with id/name (source ckan) {2}'.format(i, dataset_num, dataset_id))
            package = src_ckan.get_package(dataset_id)
            if not package:
                log.error("No dataset found with id/name = {0}".format(dataset_id))
                continue
            dataset_obj = load_from_dict(package)
            
            if org_id_name:
                org_name = org_id_name
            else:
                organization = dataset_obj.organization
                org_name = organization.get('name')

            phase = '[Obtaining dataset]'
            try:
                found, dst_package_id = dst_ckan.package_search_by_name(dataset_obj)
                # get information (name) about organization from source
                phase = '[Obtaining organization]'
                found_organization, __ = dst_ckan.find_organization(org_name)

                if not found_organization:
                    phase = '[Creating organization]'
                    result = dst_ckan.organization_create(org_name)
                    # set comsode organization id
                    dataset_obj.owner_org = result['id']
                else:
                    phase = '[Obtaining organization]'
                    result = dst_ckan.organization_show(org_name)
                    dataset_obj.owner_org = result['id']

                filter_package_extras(dataset_obj, whitelist_package_extras)

                if found:
                    phase = '[Updating dataset]'
                    dst_package_id = dst_ckan.package_update_data(dataset_id, dataset_obj.tojson_without_resource())[
                        'id']
                    log.debug('[{0} / {1}] dataset_obj with id/name {2} updated OK'.format(i, dataset_num, dataset_id))
                else:
                    phase = '[Creating dataset]'
                    dst_package_id = dst_ckan.package_create(dataset_obj)['id']
                    log.debug('[{0} / {1}] dataset_obj {2} created OK'.format(i, dataset_num, dataset_id))
                
                # now resource_names
                resource_names = []
                for resource in dataset_obj.resources:
                    if not resource['name']:
                        resource['name'] = ''
                    
                    phase = '[Creating / updating resource with name \'{0}\']'.format(resource['name'])
                    log.debug('creating / updating resource: name={0}'.format(resource['name'].encode('utf8')))
                    resource_create_update_with_upload(dst_ckan, resource, dst_package_id, whitelist_resource_extras)
                    resource_names.append(resource['name'])
                
                phase = '[Deleting resources]'
                log.debug('deleting resources with names not in {0}'.format(resource_names))
                # delete resource not in src_ckan
                dst_ckan.delete_resources_not_with_name_in(resource_names, dst_package_id)
                
                    
            except Exception,e:
                msg = '{0} {1}'.format(phase, str(e))
                if isinstance(e, urllib2.HTTPError):
                    log.error('error response: {0}'.format(e.fp.read()))
                log.error(msg)
                errors.append(msg)
        return errors
    
    
  
