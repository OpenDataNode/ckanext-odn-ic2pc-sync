'''
Created on 11.12.2014

@author: mvi
'''

import urllib2

import logging
from odn_ckancommons.JSON_Dataset import resource_create_update_with_upload,\
            load_from_dict, filter_package_extras
import urllib
import json
log = logging.getLogger('ckanext')

DATASTORE_CHUNK_SIZE = 100000

class CkanSync():
    

    def push(self, src_ckan, dst_ckan, package_ids=None,
             whitelist_package_extras=None,
             whitelist_resource_extras=None,
             org_id_name=None,
             can_create_org=False):
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
        :param can_create_org: should create organization when it doesn't exist in destination ckan
        :type can_create_org: boolean
        
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
                    if can_create_org:
                        phase = '[Creating organization]'
                        result = dst_ckan.organization_create(org_name)
                        # set comsode organization id
                        dataset_obj.owner_org = result['id']
                    else:
                        raise Exception("Couldn't find organization {0}".format(org_name))
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
                    phase = '[Resource name check]'
                    if not resource['name']:
                        e = Exception('Failed to synchronize resource: name is missing!')
                        errors.append(process_error(phase, e))
                        continue
                    
                    resource_names.append(resource['name'])
                    
                    try:
                        phase = '[Creating / updating resource with name \'{0}\']'.format(resource['name'])
                        log.debug('creating / updating resource: name={0}'.format(resource['name'].encode('utf8')))
                        response = resource_create_update_with_upload(dst_ckan, resource, dst_package_id, whitelist_resource_extras)
                        
                        if is_datastore_resource(response):
                            phase = '[Create / update of datastore resource with name \'{0}\']'.format(resource['name'])
                            log.debug('creating / updating datastore resource')
                            update_datastore_resource(src_ckan, dst_ckan, resource, response)
                    except Exception, e:
                        errors.append(process_error(phase, e))
                
                phase = '[Deleting resources]'
                log.debug('deleting resources with names not in {0}'.format(resource_names))
                # delete resource not in src_ckan
                del_errs = dst_ckan.delete_resources_not_with_name_in(resource_names, dst_package_id)
                log_errors(del_errs)
                errors += del_errs                
                    
            except Exception, e:
                errors.append(process_error(phase, e))
        return errors


def process_error(phase, e):
    ''' Logs the error and return formatted error msg
    '''
    if isinstance(e, urllib2.HTTPError):
        log.error('error response: {0}'.format(e.fp.read()))
    else:
        log.error(e)
    return '{0} {1}'.format(phase, str(e))


def log_errors(errors):
    for e in errors:
        log.error(e)

    
def is_datastore_resource(resource):
    return resource.get('url_type', False) and resource.get('url_type', '') == 'datastore'


def update_datastore_resource(src_ckan, dst_ckan, src_resource, dst_resource):
    src_res_id = src_resource['id']
    
    # just to get fields
    datastore_res, total = get_datastore_resource(src_ckan, src_res_id, limit=0)
    
    # we dont want the internal _id field
    fields = [field['id'] for field in datastore_res['fields'] if field['id'] != '_id']
    datastore_res, total = get_datastore_resource(src_ckan, src_res_id, fields=fields)
    
    is_initialized = False
    try:
        get_datastore_resource(dst_ckan, dst_resource['id'], limit=0)
        is_initialized = True
    except urllib2.HTTPError, e:
        if e.code == 400: # Bad Request
            raise Exception('Destination catalog has no datastore configured!')
        if e.code != 404: # raise except NotFound error
            raise e
    
    if not is_initialized:
        data_dict = {
            'force':True,
            'resource_id': dst_resource['id'],
            'fields': datastore_res['fields'],
            'records': datastore_res['records'],
            'primary_key': datastore_primary_key(src_ckan, src_res_id),
            'indexes': []
        }
        # create + first chunk
        resp = dst_ckan.datastore_create(data_dict)

        datastore_upsert_in_chunks(src_ckan, src_res_id,
                                   dst_ckan, dst_resource['id'],
                                   total)
    else:
        # first chunk
        resp = datastore_upsert_in_chunks(src_ckan,
                                          datastore_res['records'],
                                          dst_ckan,
                                          dst_resource['id'],
                                          total)
        # all the others if there is any
        datastore_upsert_in_chunks(src_ckan,
                                   src_res_id,
                                   dst_ckan,
                                   dst_resource['id'],
                                   total)
        # TODO remove records not updated?

def datastore_primary_key(ckan, id):
    # this isn't standard api call
    # this will function only on ckan with this plugin
    url = ckan.url + '/api/action/datastore_primary_key'
    data_dict = { 'id':id }
    data_string = urllib.quote(json.dumps(data_dict))
    return ckan.send_request(data_string, url)



def get_datastore_resource(ckan, resource_id, fields=None, offset=0, limit=DATASTORE_CHUNK_SIZE):
    search_parameters_dict = {
        'resource_id':resource_id,
        'limit': limit,
        'offset': offset
    }
    if fields:
        search_parameters_dict['fields'] = fields
    
    datastore_res = ckan.datastore_search(search_parameters_dict)
    
    return datastore_res, datastore_res.get('total', None)


def datastore_upsert_in_chunks(src_ckan, src_resource_id, dst_ckan, dst_resource_id, total):
    offset = DATASTORE_CHUNK_SIZE
    while offset < total:
        res_chunk = get_datastore_resource(src_ckan, src_resource_id,
                                           limit=DATASTORE_CHUNK_SIZE,
                                           offset=offset)
        records = res_chunk['records']
        resp = datastore_upsert(src_ckan,
                                records,
                                dst_ckan,
                                dst_resource_id)
        offset += DATASTORE_CHUNK_SIZE


def datastore_upsert(src_ckan, records, dst_ckan, dst_resource_id):
    data_dict = {
        'force':True,
        'resource_id': dst_resource_id,
        'records': records,
    }
    log.debug('upsert 100k records')
    return dst_ckan.datastore_upsert(data_dict)
    
    