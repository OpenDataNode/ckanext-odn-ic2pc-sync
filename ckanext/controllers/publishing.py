'''
Created on 12.11.2014

@author: mvi
'''

import logging
import pylons.config as config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.plugins
import ckan.logic as logic
import ckan.model as model

from ckan.common import _, request, c
from ckanext.model.external_catalog import ExternalCatalog, STATUS
from urllib2 import URLError
from odn_ckancommons.ckan_helper import CkanAPIWrapper
from ckanext.publishing.ckan_sync import CkanSync
from datetime import datetime
from ckanext.publishing.plugin import sync_ext_catalog
from ckan.logic.validators import url_validator

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

render = base.render
abort = base.abort
lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin
check_access = logic.check_access
get_action = logic.get_action

log = logging.getLogger('ckanext')

src_ckan = config.get('odn.ic2pc.src.ckan.url', None)
dst_ckan = config.get('odn.ic2pc.dst.ckan.url', None)
dst_api_key = config.get('odn.ic2pc.dst.ckan.api.key', None)
package_extras_whitelist = config.get('odn.ic2pc.package.extras.whitelist', '').split(' ')
resource_extras_whitelist = config.get('odn.ic2pc.resource.extras.whitelist', '').split(' ')


def get_url_without_slash_at_the_end(url):
    if url and url.endswith("/"):
        return url[:-1]
    else:
        return url


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
        return self._edit(id)
    
    
    def edit(self, id, cat_id):
        return self._edit(id, {'catalog':ExternalCatalog.by_id(cat_id)})
    
        
    def _edit(self, id, extra_vars={}, with_load=True):
        if with_load:
            self._load(id)
        extra_vars['form_action'] = 'save'
        return render('publishing/edit.html', extra_vars = extra_vars)
    
    
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


    def verify(self, id, data, vars):
        cat_id, type, url, auth_req, auth, org_id, create_as_private = data
        has_errors = len(vars) > 0
            
        vars['cat_id'] = cat_id
        vars['type'] = type
        vars['url_val'] = url
        vars['req_auth'] = auth_req
        vars['auth'] = auth
        vars['org_id'] = org_id
        vars['create_as_private'] = create_as_private
        
        log.debug("CREATE AS PRIVATE = {0}".format(create_as_private))
        
        if has_errors :
            return self._edit(id, vars)
        
        self._load(id)
        if type == 'CKAN':
            if auth_req:
                ext_cat = CkanAPIWrapper(url, auth)
            else:
                ext_cat = CkanAPIWrapper(url, None)
            
            # check if catalog is available
            read_ok, redirected_to = ext_cat.site_read()
            if not read_ok:
                vars['url_error'] = [_('Could not connect to this catalog.')]
                return self._edit(id, vars, False)
            
            if redirected_to:
                h.flash_notice(_('The verification was redirected to \'{0}\'. '
                    'The synchronization may not function properly. Try to '
                    'replace URL for the redirected url.').format(redirected_to))
            
            # check organization
            check_org = org_id or c.pkg_dict.get('owner_org', None)
            org = ext_cat.organization_show2(check_org)
            if not org:
                vars['org_error'] = [_('Organization with this id or name was not found.')]
                return self._edit(id, vars, False)
            
            # chech authorization
            if not ext_cat.has_edit_rights(check_org):
                if auth_req:
                    vars['auth_error'] = [_('User with this API key is not authorized to edit datasets for organization {0}').format(org['name'])]
                else:
                    vars['auth_req_error'] = [_('This catalog requires authorization for organization {0}.').format(org['name'])]
                return self._edit(id, vars, False)

            vars['verified'] = True
            h.flash_success(_("External catalog verification was successful."))
            return self._edit(id, vars, False)
        else:
            h.flash_notice(_("Verify is not supported for type {0}").format(type))
            return self._edit(id, vars, False)
    
    
    def _validate_url(self, url):
        errors = {'url':[]}
        url_validator('url', {'url':url}, errors, {'model':None, 'session':None})
        
        if errors['url']:
            return errors['url'][0]


    def save(self, id):
        data = request.POST
        cat_id = data[u'catalog_id']
        type = data.get(u'type', '')
        url = get_url_without_slash_at_the_end(data.get(u'url', ''))
        org_id = data.get(u'org_id', '')
        auth_req = False
        create_as_private = False
        if u'authorization_required' in data:
            auth_req = True
        if u'create_as_private' in data:
            create_as_private = True
        auth = data[u'authorization']
        
        err_msg = [_("This field is required")]
        extra_vars = {}
        if not type:
            extra_vars['type_error'] = err_msg
        if not url:
            extra_vars['url_error'] = err_msg
        if auth_req and not auth:
            extra_vars['auth_error'] = err_msg
            
        url_validation_err = self._validate_url(url)
        if url_validation_err:
            extra_vars['url_error'] = [url_validation_err]
        elif not cat_id and ExternalCatalog.has_catalog(id, url):
            extra_vars['url_error'] = [_('This dataset already has external catalog with this URL')]
        
        if data.get('action', None) == 'verify':
            return self.verify(id, (cat_id, type, url, auth_req, auth, org_id, create_as_private), extra_vars)
        
        
        if extra_vars:
            extra_vars['cat_id'] = cat_id
            extra_vars['type'] = type
            extra_vars['url_val'] = url
            extra_vars['req_auth'] = auth_req
            extra_vars['auth'] = auth
            extra_vars['org_id'] = org_id
            return self._edit(id, extra_vars)
            
        try:
            if not cat_id:
                ext_catalog = ExternalCatalog(id, type, url, auth_req, auth, ext_org_id=org_id, create_as_private=create_as_private)
            else:
                ext_catalog = ExternalCatalog.by_id(cat_id)
                ext_catalog.type = type
                ext_catalog.url = url
                ext_catalog.authorization_required = auth_req
                ext_catalog.authorization = auth
                ext_catalog.ext_org_id = org_id
                ext_catalog.create_as_private = create_as_private
            
            ext_catalog.save()
            h.flash_success(_("Successfully created / edited catalog {url}").format(url=url))
        except Exception, e:
            err_msg = str(e)
            log.exception(e)
            h.flash_error(_("Error: couldn't add catalog, cause: {err_msg}"\
                            .format(err_msg=err_msg)))
        
        pkg = model.Package.get(id)
        base.redirect(h.url_for('dataset_publishing', id=pkg.name))
        
        
    def sync_public(self, id):
        self._load(id)
        if not c.pkg_dict['private']:
            sync(c.pkg_dict)
            h.flash_notice(_('Synchronization with public catalog ended.'))
        else:
            h.flash_notice(_("Synchronization not started, the dataset isn't public."))
        base.redirect(h.url_for('dataset_publishing', id=id))
    
    
    def sync_all_ext(self, id):
        self._load(id)
        if not c.pkg_dict['private']:
            sync(c.pkg_dict, False)
            h.flash_notice(_('Synchronization with external catalogs ended.'))
        else:
            h.flash_notice(_("Synchronization not started, the dataset isn't public."))
        base.redirect(h.url_for('dataset_publishing', id=id))


    def sync_ext(self, id, cat_id):
        self._load(id)
        log.debug("syncronizing specific ext catalog {0}".format(cat_id))
        if not c.pkg_dict['private']:
            from_ckan = CkanAPIWrapper(src_ckan, None)
            ext_cat = ExternalCatalog.by_id(cat_id)
            errors = []
            errs = sync_ext_catalog(from_ckan, ext_cat, c.pkg_dict)
            for err in errs:
                errors.append('{0} - {1}'.format(ext_cat.url, err))
            flash_errors_for_ext_cat(errors)
            h.flash_notice(_('Synchronization with public catalog ended.'))
        else:
            h.flash_notice(_("Synchronization not started, the dataset isn't public."))
        base.redirect(h.url_for('dataset_publishing', id=id))
        
    
def sync(dataset, public=True):
    from_ckan = CkanAPIWrapper(src_ckan, None)
    
    if public: # public catalog from .ini file
        try:
            log.debug("sync to public CKAN: {0}".format(dst_ckan))
            default_dst_ckan = CkanAPIWrapper(dst_ckan, dst_api_key)
            
            errors = CkanSync().push(from_ckan, default_dst_ckan, [dataset['name']],
                        package_extras_whitelist, resource_extras_whitelist,
                        can_create_org=True)
            if errors:
                msg = '<p>Error occured while synchronizing catalog:</p><ul>'
                for err in errors:
                    msg += '<li>public catalog - {0}</li>'.format(err)
                msg += '</ul>'
                h.flash_error(msg, True)
        except URLError, e:
            log.error("Couldn't finish synchronization: {0}".format(e))
        except Exception, e:
            log.exception(e)
    else: # external catalogs
        ext_catalogs = ExternalCatalog.by_dataset_id(dataset['id'])
        log.debug("sync to dataset specified external catalogs ({0})".format(len(ext_catalogs)))
        
        errors = []
        for catalog in ext_catalogs:
            errs = sync_ext_catalog(from_ckan, catalog, dataset)
            for err in errs:
                errors.append('{0} - {1}'.format(catalog.url, err))
        
        flash_errors_for_ext_cat(errors)

def flash_errors_for_ext_cat(errors):
    if errors:
        msg = '<p>Error occured while synchronizing external catalog:</p><ul>'
        for err in errors:
            msg += '<li>{0}</li>'.format(err)
        msg += '</ul>'
        h.flash_error(msg, True)
    