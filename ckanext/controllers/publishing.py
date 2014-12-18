'''
Created on 12.11.2014

@author: mvi
'''

import logging

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.plugins
import ckan.logic as logic
import ckan.model as model

from ckan.common import _, request, c
from ckanext.model.external_catalog import ExternalCatalog

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

render = base.render
abort = base.abort
lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin
check_access = logic.check_access
get_action = logic.get_action

log = logging.getLogger('ckanext')


class PublishingController(base.BaseController):

    
    def _get_package_type(self, id):
        """
        Given the id of a package it determines the plugin to load
        based on the package's type name (type). The plugin found
        will be returned, or None if there is no plugin associated with
        the type.
        """
        pkg = model.Package.get(id)
        if pkg:
            return pkg.type or 'dataset'
        return None


    def _load(self, id):
        package_type = self._get_package_type(id.split('@')[0])
        data_dict = {'id': id}
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        
        try:
            check_access('package_update', context, data_dict)
        except NotAuthorized, e:
            abort(401, _('User {user} not authorized to edit {id}').format(user=c.user, id=id))
        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package {id}').format(id=id))
        
        lookup_package_plugin(package_type).setup_template_variables(context, {'id': id})
    
    
    def show(self, id):
        self._load(id)
        vars = {
                'catalogs': ExternalCatalog.by_dataset_id(c.pkg_dict['id'])
        }
        return render('package/publishing.html', extra_vars = vars)
    
    
    def create(self, id):
        self._load(id)
        vars = {
                'form_action': 'save',
        }
        return render('publishing/edit.html', extra_vars = vars)
    
    
    def edit(self, id, cat_id):
        self._load(id)
        vars = {
                'form_action': 'save', # TODO
                'catalog': ExternalCatalog.by_id(cat_id)
        }
        return render('publishing/edit.html', extra_vars = vars)
    
    
    def delete(self, id, cat_id):
        # this is just the confirmation page
        self._load(id)
        vars = {
                'catalog': ExternalCatalog.by_id(cat_id)
        }
        return render('publishing/delete.html', extra_vars = vars)


    def delete_cat(self, id, cat_id):
        # this is the actual deletion
        log.debug("deleting ext catalog {0}".format(cat_id))
        
        try:
            catalog = ExternalCatalog.by_id(cat_id)
            catalog.delete()
            catalog.commit()
            h.flash_success(_('Catalog deleted successfully.'))
        except Exception, e:
            err_msg = str(e)
            h.flash_error(_("Error: couldn't delete catalog, cause: {err_msg}"\
                            .format(err_msg=err_msg)))
        
        base.redirect(h.url_for('dataset_publishing', id=id))


    def save(self, id):
        data = request.POST
        type = data[u'type']
        url = data['url']
        auth_req = False
        if u'authorization_required' in data:
            auth_req = True
        auth = data[u'authorization']
        
        missing = []
        if not type:
            missing.append(_("Type of catalog"))
        if not url:
            missing.append(_("URL of external catalog"))
        if auth_req and not auth:
            missing.append(_("Authorization"))
        
        if missing:
            h.flash_error(_("This fields are required and need to be filled: {0}")\
                          .format(', '.join(missing)))
            redirect_to_page = 'create_catalog'
            if data[u'catalog_id']:
                base.redirect(h.url_for('edit_catalog', id=id, cat_id=data[u'catalog_id']))
            else:
                base.redirect(h.url_for('create_catalog', id=id))
            
        try:
            # TODO
            
            if not data[u'catalog_id']:
                ext_catalog = ExternalCatalog(id, type, url, auth_req, auth)
            else:
                ext_catalog = ExternalCatalog.by_id(data[u'catalog_id'])
                ext_catalog.type = type
                ext_catalog.url = url
                ext_catalog.authorization_required = auth_req
                ext_catalog.authorization = auth
            
            ext_catalog.save()
            h.flash_success(_("Successfully created / edited catalog {url}").format(url=url))
        except Exception, e:
            err_msg = str(e)
            log.exception(e)
            h.flash_error(_("Error: couldn't add catalog, cause: {err_msg}"\
                            .format(err_msg=err_msg)))
        
        pkg = model.Package.get(id)
        base.redirect(h.url_for('dataset_publishing', id=pkg.name))
