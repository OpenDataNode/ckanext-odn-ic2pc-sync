
import ckanext.datastore.db as db
import ckan.logic as logic
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import pylons.config as config
import routes.mapper
import logging
import threading

from ckan.logic.action.update import package_update
from ckan.logic.action.create import package_create
from ckanext.model.external_catalog import ExternalCatalog, STATUS
from odn_ckancommons.ckan_helper import CkanAPIWrapper
from ckanext.publishing.ckan_sync import CkanSync
from urllib2 import URLError
from datetime import datetime

from multiprocessing.synchronize import Lock
from Queue import Queue
lock = Lock()

log = logging.getLogger('ckanext')

GET = dict(method=['GET'])
POST = dict(method=['POST'])
NotFound = toolkit.ObjectNotFound

get_action = logic.get_action

def worker():
    while True:
        item = queue.get()
        start_sync(item)
        queue.task_done()
  
class SetQueue(Queue):
  
    def _init(self, maxsize):
        Queue._init(self, maxsize)
        self.all_items = set()
        log.debug("SetQueue init")
  
    def _put(self, item):
        pkg_name = item['name']
          
        if pkg_name not in self.all_items:        
            self.all_items.add(pkg_name)
            Queue._put(self, item)
  
    def _get(self):
        item = Queue._get(self)
        pkg_name = item['name']
        self.all_items.discard(pkg_name)
        return item
 
queue = SetQueue()
t = threading.Thread(target=worker)
t.daemon = True
t.start()
 

def get_url_without_slash_at_the_end(url):
    if url and url.endswith("/"):
        return url[:-1]
    else:
        return url

src_ckan = get_url_without_slash_at_the_end(config.get('odn.ic2pc.src.ckan.url', None))
dst_ckan = get_url_without_slash_at_the_end(config.get('odn.ic2pc.dst.ckan.url', None))
dst_api_key = config.get('odn.ic2pc.dst.ckan.api.key', None)
package_extras_whitelist = config.get('odn.ic2pc.package.extras.whitelist', '').split(' ')
resource_extras_whitelist = config.get('odn.ic2pc.resource.extras.whitelist', '').split(' ')

def check_and_bust(key, dict):
    if key not in dict or not dict[key]:
        raise NotFound("Key '{0}' was not found or has no value set.".format(key))

def get_catalogs_to_sync(dataset):
    # we need package_id!
    package_id = dataset['id']
    ext_catalogs = ExternalCatalog.by_dataset_id(package_id)
    return ext_catalogs


@toolkit.side_effect_free
def datastore_primary_key(context, data_dict=None):
    """Checks primary keys for resource, has to have rights to display dataset
    
    :param id: resource id
    :return: list of strings - primary key column names
    """
    check_and_bust('id', data_dict)
    id = data_dict['id']
    toolkit.check_access('resource_show', context, data_dict)
    
    data_dict['connection_url'] = config['ckan.datastore.write_url']
    engine = db._get_engine(data_dict)
    context['connection'] = engine.connect()
    
    data_dict = {'resource_id':id}
    try:
        p_keys = db._get_unique_key(context, data_dict)
    finally:
        context['connection'].close()
    
    return p_keys

def start_sync(dataset):
    assert dataset
     
    try:
        log.debug('>>> starting sync of dataset = {0}'.format(dataset['name']))
        catalogs = get_catalogs_to_sync(dataset)
         
        from_ckan = CkanAPIWrapper(src_ckan, None)
        default_dst_ckan = CkanAPIWrapper(dst_ckan, dst_api_key)
             
        log.debug("sync to default CKAN: {0}".format(dst_ckan))
        try:
            CkanSync().push(from_ckan, default_dst_ckan, [dataset['name']],
                            package_extras_whitelist, resource_extras_whitelist,
                            can_create_org=True)
        except URLError, e:
            log.error("Couldn't finish synchronization: {0}".format(e))
        except Exception, e:
            log.exception(e)
             
        log.debug("sync to dataset specified external catalogs ({0})".format(len(catalogs)))
        for catalog in catalogs:
            sync_ext_catalog(from_ckan, catalog, dataset)
             
        log.debug('<<< end of synchronization')
    except Exception, e:
        log.error(e)


def sync_ext_catalog(from_ckan, external_catalog, dataset):
    '''Synchronizes dataset from from_ckan to external_catalog
    
    :param from_ckan: source ckan
    :type from_ckan: CkanAPIWrapper
    :param external_catalog: destination CKAN
    :type external_catalog: ExternalCatalog
    :param dataset: dataset to push / synchronize
    :type dataset: dictionary
    '''
    status = STATUS.index("OK")
    errors = []
    authorization = None
    try:
        if external_catalog.type == 'CKAN':
            log.debug('sync to catalog = {0}'.format(external_catalog.url))
            
            if external_catalog.authorization_required:
                authorization = external_catalog.authorization
            
            to_ckan = CkanAPIWrapper(external_catalog.url, authorization)
            errors = CkanSync().push(from_ckan, to_ckan, [dataset['name']], \
                                    package_extras_whitelist, resource_extras_whitelist, \
                                    org_id_name=external_catalog.ext_org_id, \
                                    create_pkg_as_private=external_catalog.create_as_private)
            if errors:
                status = STATUS.index("FAILED")
        else:
            log.debug('Catalog {0} is not CKAN type'.format(external_catalog.url))
    except URLError, e:
        status = STATUS.index("FAILED")
        log.exception(e)
        errors = ["Couldn't finish synchronization: {0}".format(e.reason)]
    except Exception, e:
        status = STATUS.index("FAILED")
        log.exception(e)
        errors = ["Couldn't finish synchronization: {0}".format(e)]
        
    external_catalog.last_updated = datetime.utcnow()
    external_catalog.status = status
    external_catalog.save()
    return errors
        

def dataset_update(context, data_dict=None):
    # catches also resource_update, resource_create, resource_delete
    ret_val = package_update(context, data_dict)
    
    if not ret_val['private']:
        log.debug("package_update sync dataset")
        queue.put(ret_val)
        
    return ret_val


def dataset_create(context, data_dict=None):
    ret_val = package_create(context, data_dict)

    if not ret_val['private']:
        log.debug("package_create sync dataset")
        queue.put(ret_val)
        
    return ret_val


def format_datetime(datetime):
    
    if not datetime:
        return None

    return datetime.strftime("%d. %b %Y, %H:%M")


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
                'datastore_primary_key':datastore_primary_key}

    
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
            
            m.connect('/dataset/{id}/publishing/sync_public', action='sync_public')
            m.connect('/dataset/{id}/publishing/sync_all_ext', action='sync_all_ext')
            m.connect('/dataset/{id}/publishing/sync_ext/{cat_id}', action='sync_ext')
        
        return route_map
    
    
    def after_map(self, route_map):
        # see IRoutes plugin interface
        return route_map