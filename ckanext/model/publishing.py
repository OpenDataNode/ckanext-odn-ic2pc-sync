'''
Created on 11.11.2014

@author: mvi
'''


from sqlalchemy.sql.expression import or_
from sqlalchemy import types, Column, Table, ForeignKey
import vdm.sqlalchemy

import types as _types
from ckan.model import domain_object
from ckan.model.meta import metadata, Session, mapper
from sqlalchemy.orm import relationship, backref
from ckan.model.package import Package


external_catalog_table = Table('external_catalog', metadata,
            Column('id', types.INTEGER, primary_key=True, autoincrement=True),
            Column('package_id', ForeignKey('package.id'), nullable=False, unique=False),
            Column('type', types.UnicodeText, nullable=False),
            Column('url', types.UnicodeText, nullable=False),
            Column('authorization_required', types.BOOLEAN, nullable=False),
            Column('authorization', types.UnicodeText, nullable=True)
            )


class ExternalCatalog(domain_object.DomainObject):
    
    def __init__(self, package_id, type, url, authorization_required, authorization):
        assert package_id
        assert type
        assert url
        assert authorization_required is not None
        self.package_id = package_id
        self.type = type
        self.url = url
        self.authorization_required = authorization_required
        self.authorization  = authorization
    
    @classmethod
    def get_all(cls):
        return Session.query(cls).order_by(cls.id)
    
    @classmethod
    def by_dataset_id(cls, dataset_id):
        assert dataset_id
        return Session.query(cls)\
            .filter_by(package_id = dataset_id).order_by(cls.id)
    
    @classmethod
    def by_id(cls, id):
        assert id
        return Session.query(cls).filter_by(id=id).first()
            

mapper(ExternalCatalog, external_catalog_table, properties={
    "external_catalog": relationship(Package, single_parent=True, backref=backref('external_catalog', cascade="all, delete, delete-orphan"))
})