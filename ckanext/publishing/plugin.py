
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config
import routes.mapper
import logging
import threading

from ckan.logic.action.update import package_update, resource_update
from ckan.logic.action.create import package_create, resource_create
from ckanext.model.external_catalog import ExternalCatalog
from odn_ckancommons.ckan_helper import CkanAPIWrapper
from ckanext.publishing.ckan_sync import CkanSync
from urllib2 import URLError
from datetime import datetime
log = logging.getLogger('ckanext')

GET = dict(method=['GET'])
POST = dict(method=['POST'])

get_action = logic.get_action


src_ckan = config.get('odn.ic2pc.src.ckan.url', None)
dst_ckan = config.get('odn.ic2pc.dst.ckan.url', None)
dst_api_key = config.get('odn.ic2pc.dst.ckan.api.key', None)
package_extras_whitelist = config.get('odn.ic2pc.package.extras.whitelist', '').split(' ')
resource_extras_whitelist = config.get('odn.ic2pc.resource.extras.whitelist', '').split(' ')



def get_catalogs_to_sync(dataset):
    # we need package_id!
    package_id = dataset['id']
    ext_catalogs = ExternalCatalog.by_dataset_id(package_id)
    return ext_catalogs


def start_sync(context, dataset):
    assert dataset # TODO proper error throw
    
    log.debug('starting sync of dataset = {0}'.format(dataset['name']))
    catalogs = get_catalogs_to_sync(dataset)

    from_ckan = CkanAPIWrapper(src_ckan, None)
    default_dst_ckan = CkanAPIWrapper(dst_ckan, dst_api_key)
    
    log.debug("sync to default CKAN: {0}".format(dst_ckan))
    try:
        CkanSync().push(from_ckan, default_dst_ckan, [dataset['name']],
                        package_extras_whitelist, resource_extras_whitelist)
    except URLError, e:
        log.error("Couldn't finish synchronization: {0}".format(e))
    except Exception, e:
        log.exception(e)
    
    log.debug("sync to dataset specific extra external catalogs ({0})".format(len(catalogs)))
    for catalog in catalogs:
        try:
            if catalog.type == 'CKAN':
                log.debug('sync to catalog = {0}'.format(catalog.url))
                to_ckan = CkanAPIWrapper(catalog.url, catalog.authorization)
                CkanSync().push(from_ckan, to_ckan, [dataset['name']], package_extras_whitelist, resource_extras_whitelist)
                catalog.last_updated = datetime.utcnow()
                catalog.save()
            else:
                log.debug('Catalog {0} is not CKAN type'.format(catalog.url))
        except URLError, e:
            log.error("Couldn't finish synchronization: {0}".format(e))
        except Exception, e:
            log.exception(e)


def dataset_update(context, data_dict=None):
    ret_val = package_update(context, data_dict)
    if not context.get('defer_commit') and not ret_val['private']:
        log.debug("package_update sync dataset TODO")
        t = threading.Thread(target=start_sync, args=(context, ret_val, ))
        t.daemon = True
        t.start()
        
    return ret_val


def dataset_create(context, data_dict=None):
    ret_val = package_create(context, data_dict)

    if not context.get('defer_commit') and not ret_val['private']:
        log.debug("package_create sync dataset TODO")
        t = threading.Thread(target=start_sync, args=(context, ret_val, ))
        t.daemon = True
        t.start()
        
    return ret_val


def res_create(context, data_dict=None):
    ret_val = resource_create(context, data_dict)
    package_id = context['package'].name
    
    data_dict = {'id': package_id}
    dataset = get_action('package_show')(context, data_dict)
    if not dataset['private']: # dataset is public
        log.debug("resource_create sync dataset TODO")
        t = threading.Thread(target=start_sync, args=(context, dataset, ))
        t.daemon = True
        t.start()
    
    return ret_val


def res_update(context, data_dict=None):
    ret_val = resource_update(context, data_dict)
    package_id = context['package'].name

    data_dict = {'id': package_id}
    dataset = get_action('package_show')(context, data_dict)
    if not dataset['private']: # dataset is public
        log.debug("resource_update sync dataset TODO")
        t = threading.Thread(target=start_sync, args=(context, dataset, ))
        t.daemon = True
        t.start()
        
    return ret_val


def format_datetime(datetime):
    
    if not datetime:
        return None

    return datetime.strftime("%Y-%m-%d %H:%M")


class PublishingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)


    def get_helpers(self):
        return {'format_datetime': format_datetime}
        
    
    def get_actions(self):
        return {'package_create': dataset_create,
                'package_update': dataset_update,
                'resource_create': res_create,
                'resource_update': res_update}

    
    def update_config(self, config):
        # see IConfigurer plugin interface
        
        # Tells CKAN to use the template and
        # snippet files
        toolkit.add_template_directory(config, 'templates')
        
        # Tells CKAN where to find JS and CSS files
        toolkit.add_resource('fanstatic', 'publ_theme')

        
    def before_map(self, route_map):
        # see IRoutes plugin interface
        with routes.mapper.SubMapper(route_map,
                controller='ckanext.controllers.publishing:PublishingController') as m:
            
            m.connect('dataset_publishing', '/dataset/{id}/publishing', action='show', conditions=GET)
            m.connect('create_catalog', '/dataset/{id}/publishing/create_catalog', action='create')
            m.connect('edit_catalog', '/dataset/{id}/publishing/edit_catalog/{cat_id}', action='edit')
            m.connect('/dataset/{id}/publishing/save_cat', action='save', conditions=POST)
            
            m.connect('/dataset/{id}/publishing/delete/{cat_id}', action='delete')
            m.connect('/dataset/{id}/publishing/delete_catalog/{cat_id}', action='delete_cat', conditions=POST)
        
        return route_map
    
    
    def after_map(self, route_map):
        # see IRoutes plugin interface
        return route_map