import sqlalchemy

# from flask_sqlalchemy import BaseQuery
from hivclinic import db
from sqlalchemy.dialects.postgresql import UUID
import datetime
from flask import current_app


# class QueryWithSoftDelete(BaseQuery):
#     """
#     https://blog.miguelgrinberg.com/post
#     /implementing-the-soft-delete-pattern-with-flask-and-sqlalchemy
#     """

#     def __new__(cls, *args, **kwargs):
#         obj = super(QueryWithSoftDelete, cls).__new__(cls)

#         with_deleted = kwargs.pop("_with_deleted", False)
#         only_deleted = kwargs.pop("_only_deleted", False)

#         if len(args) > 0:
#             super(QueryWithSoftDelete, obj).__init__(*args, **kwargs)

#             if only_deleted:
#                 return obj.filter_by(deleted=True)

#             elif with_deleted:
#                 return obj

#             else:
#                 return obj.filter_by(deleted=False)

#         return obj

#     def __init__(self, *args, **kwargs):
#         pass

#     def with_deleted(self):
#         return self.__class__(
#             db.class_mapper(self._mapper_zero().class_),
#             session=db.session(),
#             _with_deleted=True,
#         )

#     def only_deleted(self):
#         return self.__class__(
#             db.class_mapper(self._mapper_zero().class_),
#             session=db.session(),
#             _only_deleted=True,
#         )


class BaseModel(db.Model):
    __abstract__ = True

    # implement soft delete
    # query_class = QueryWithSoftDelete

    # define protected keys
    do_not_update_keys = set(
        [
            "id",
            # "deleted",
            "created_on",
            "_sa_instance_state",
            "do_not_update_keys",
            "protected_keys",
            "relationship_keys",
            "query_class",
            "imported",
        ]
    )
    protected_keys = set([])
    relationship_keys = set([])

    # common keys
    id = db.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sqlalchemy.text("uuid_generate_v4()"),
    )

    created_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    modified_on = db.Column(
        db.DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # deleted = db.Column(db.Boolean, default=False)
    imported = db.Column(db.Boolean, default=False)

    # common methods
    def __repr__(self):
        return "<BaseModel(name={self.__class__.__name__!r})>".format(
            self=self
        )

    def __str__(self):
        return str(self.__repr__)

    @classmethod
    def all_subclasses(cls):
        return cls.__subclasses__() + [
            g for s in cls.__subclasses__() for g in s.all_subclasses()
        ]

    def all_keys(self):
        return set(vars(self).keys())

    def update(self, **kwargs):
        if isinstance(self.protected_keys, (list, tuple)):
            self.protected_keys = set(self.protected_keys)

        if isinstance(self.relationship_keys, (list, tuple)):
            self.relationship_keys = set(self.relationship_keys)

        keys = self.all_keys()
        keys = (
            keys
            - self.do_not_update_keys
            - self.protected_keys
            - self.relationship_keys
        )

        for key in keys:
            try:
                setattr(self, key, kwargs[key])

            except (AttributeError, KeyError):
                # current_app.logger.debug(
                #     f"Skipping {key}",
                #     exc_info=current_app.config["DEBUG"],
                # )
                pass
