'''
Created on 11.11.2014

@author: mvi
'''


from sqlalchemy import types, Column, Table, ForeignKey

from ckan.model import domain_object
from ckan.model.meta import metadata, Session, mapper
from sqlalchemy.orm import relationship, backref
from ckan.model.package import Package

STATUS = ["N/A", "OK", "FAILED"]

external_catalog_table = Table('external_catalog', metadata,
            Column('id', types.INTEGER, primary_key=True, autoincrement=True),
            Column('package_id', ForeignKey('package.id'), nullable=False, unique=False),
            Column('type', types.UnicodeText, nullable=False),
            Column('url', types.UnicodeText, nullable=False),
            Column('authorization_required', types.BOOLEAN, nullable=False),
            Column('authorization', types.UnicodeText, nullable=True),
            Column('last_updated', types.DateTime, nullable=True),
            Column('status', types.SmallInteger(), nullable=False),
            Column('ext_org_id', types.UnicodeText, nullable=True),
            Column('create_as_private', types.BOOLEAN, nullable=False, default=False)
            )

def migrate_to_v0_3():
    conn = Session.connection()
    
    statement = """
    ALTER TABLE external_catalog
        ADD COLUMN last_updated timestamp,
        ADD COLUMN status smallint not null default 0;
    """
    conn.execute(statement)
    Session.commit()


def migrate_to_v0_4():
    conn = Session.connection()
    
    statement = """
    ALTER TABLE external_catalog
        ADD COLUMN ext_org_id text;
    """
    conn.execute(statement)
    Session.commit()
    
def migrate_to_v0_6():
    conn = Session.connection()
    
    statement = """
    ALTER TABLE external_catalog
        ADD COLUMN create_as_private BOOLEAN NOT NULL DEFAULT FALSE;
    """
    conn.execute(statement)
    Session.commit()
    


class ExternalCatalog(domain_object.DomainObject):
    
    def __init__(self, package_id, type, url, authorization_required, authorization, last_updated=None, status=0, ext_org_id=None, create_as_private=False):
        assert package_id
        assert type
        assert url
        assert authorization_required is not None
        self.package_id = package_id
        self.type = type
        self.url = url
        self.authorization_required = authorization_required
        self.authorization  = authorization
        self.last_updated = last_updated
        self.status = status
        self.ext_org_id = ext_org_id
        self.create_as_private = create_as_private
    
    @classmethod
    def get_all(cls):
        return Session.query(cls).order_by(cls.id).all()
    
    @classmethod
    def by_dataset_id(cls, dataset_id):
        assert dataset_id
        return Session.query(cls)\
            .filter_by(package_id = dataset_id).order_by(cls.id).all()
    
    @classmethod
    def by_id(cls, id):
        assert id
        return Session.query(cls).filter_by(id=id).first()
    
    def status_string(self):
        return STATUS[self.status]
            

mapper(ExternalCatalog, external_catalog_table, properties={
    "external_catalog": relationship(Package, single_parent=True, backref=backref('external_catalog', cascade="all, delete, delete-orphan"))
})