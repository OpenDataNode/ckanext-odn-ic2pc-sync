'''
Created on 11.12.2014

@author: mvi
'''

from odn_ckancommons.ckan_helper import CkanAPIWrapper
from ckanext.publishing.ckan_sync import CkanSync
from pprint import pprint

import logging.config

logging.config.fileConfig("logging.cfg")
src_ckan = CkanAPIWrapper('http://192.168.7.36/internalcatalog', 'cdcf70b8-b449-486c-a8f3-a50f88b8130d')
dst_ckan = CkanAPIWrapper('http://192.168.7.36', 'df9146ce-7851-4bae-8c78-0a7405a59409')

def push(from_ckan, to_ckan, org, package_ids):
    pusher = CkanSync()
    whitelist_package = ['creator', 'dataset', 'license', 'modified',
                         'publisher', 'void#sparqlEndpoint']
    whitelist_resource = ['license']

    # PUSH IT
    return pusher.push(from_ckan, to_ckan,
                        package_ids=package_ids,
                        whitelist_package_extras=whitelist_package,
                        whitelist_resource_extras=whitelist_resource,
                        org_id_name=org)

def push_all_public(from_ckan, to_ckan, org):
    package_ids = from_ckan.get_all_package_ids()
    pprint(package_ids)
    return push(from_ckan, to_ckan, org, package_ids)


resp = push_all_public(src_ckan, dst_ckan, "comsode")
pprint(resp)
