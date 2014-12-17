
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import routes.mapper

import logging
log = logging.getLogger('ckanext')


GET = dict(method=['GET'])
POST = dict(method=['POST'])


class PublishingPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes)
    
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