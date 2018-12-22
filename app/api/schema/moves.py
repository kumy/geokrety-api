import re
from string import digits, letters

from flask_rest_jsonapi.exceptions import ObjectNotFound
from marshmallow import validates, validates_schema
from marshmallow_jsonapi import fields
from marshmallow_jsonapi.flask import Relationship, Schema

import characterentities
from app.api.helpers.data_layers import MOVE_TYPES_LIST
from app.api.helpers.db import safe_query
from app.api.helpers.exceptions import UnprocessableEntity
from app.api.helpers.utilities import dasherize
from app.models.geokret import Geokret

ALLOWED_TRACKING_CODE_CHARACTERS = set(digits).union(letters)
ALLOWED_WAYPOINT_CHARACTERS = set(digits).union(letters)


class MoveSchema(Schema):

    @validates('tracking_code')
    def validate_tracking_code(self, data):
        data = characterentities.decode(data).replace('\x00', '').strip()
        if not data:
            raise UnprocessableEntity("Tracking Code cannot be blank",
                                      {'pointer': '/data/attributes/tracking-code'})

        if not all(c in ALLOWED_TRACKING_CODE_CHARACTERS for c in data):
            raise UnprocessableEntity("Tracking Code format is invalid",
                                      {'pointer': '/data/attributes/tracking-code'})
        try:
            safe_query(self, Geokret, 'tracking_code', data, 'tracking_code')
        except ObjectNotFound:
            raise UnprocessableEntity("Tracking Code is invalid",
                                      {'pointer': '/data/attributes/tracking-code'})

    @validates('application_version')
    def validate_application_version(self, data):
        if data is not None and len(data) > 16:
            raise UnprocessableEntity("Application Version is too long",
                                      {'pointer': '/data/attributes/application-version'})

    @validates('type')
    def validate_type(self, data):
        if data not in MOVE_TYPES_LIST:
            raise UnprocessableEntity("Type Id is invalid",
                                      {'pointer': '/data/attributes/type'})

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"

    id = fields.Integer(dump_only=True)
    tracking_code = fields.Str(required=True, load_only=True)
    comment = fields.Str(allow_none=True)
    username = fields.Str(dump_only=True)
    moved_on_datetime = fields.DateTime(required=True)
    application_name = fields.Str(allow_none=True)
    application_version = fields.Str(allow_none=True)
    altitude = fields.Integer(dump_only=True)
    country = fields.Str(dump_only=True)
    distance = fields.Integer(dump_only=True)
    pictures_count = fields.Integer(dump_only=True)
    comments_count = fields.Integer(dump_only=True)
    created_on_datetime = fields.DateTime(dump_only=True)
    updated_on_datetime = fields.DateTime(dump_only=True)

    author = Relationship(
        attribute='author',
        self_view='v1.move_author',
        self_view_kwargs={'id': '<id>'},
        related_view='v1.user_details',
        related_view_kwargs={'move_author_id': '<id>'},
        schema='UserSchema',
        type_='user',
        include_resource_linkage=True,
    )

    type = Relationship(
        attribute='type',
        self_view='v1.move_type',
        self_view_kwargs={'id': '<id>'},
        related_view='v1.move_type_details',
        related_view_kwargs={'move_id': '<id>'},
        schema='MovesTypesSchema',
        type_='move-type',
        include_resource_linkage=True,
    )

    geokret = Relationship(
        attribute='geokret',
        self_view='v1.move_geokret',
        self_view_kwargs={'id': '<id>'},
        related_view='v1.geokrety_type_details',
        related_view_kwargs={'move_id': '<id>'},
        schema='GeokretSchema',
        type_='geokret',
        include_resource_linkage=True,
    )




class MoveWithCoordinatesSchema(MoveSchema):

    @validates('waypoint')
    def validate_waypoint(self, data):
        if not data:
            return

        if not all(c in ALLOWED_WAYPOINT_CHARACTERS for c in data):
            raise UnprocessableEntity("Waypoint format is invalid",
                                      {'pointer': '/data/attributes/waypoint'})

    @validates('latitude')
    def validate_latitude_valid(self, data):
        pattern = re.compile("^(\+|-)?(?:90(?:(?:\.0{1,6})?)|(?:[0-9]|[1-8][0-9])(?:(?:\.[0-9]{1,6})?))$")
        if data is not None and not pattern.match(str(data)):
            raise UnprocessableEntity("Latitude is invalid",
                                      {'pointer': '/data/attributes/latitude'})

    @validates('longitude')
    def validate_longitude_valid(self, data):
        pattern = re.compile("^(\+|-)?(?:180(?:(?:\.0{1,6})?)|(?:[0-9]|[1-9][0-9]|1[0-7][0-9])(?:(?:\.[0-9]{1,6})?))$")
        if data is not None and not pattern.match(str(data)):
            raise UnprocessableEntity("Longitude is invalid",
                                      {'pointer': '/data/attributes/longitude'})

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"

    latitude = fields.Float(required=True, allow_none=False)
    longitude = fields.Float(required=True, allow_none=False)
    waypoint = fields.Str(allow_none=True)


class MoveWithCoordinatesOptionalSchema(MoveWithCoordinatesSchema):

    @validates_schema
    def validate_latitude_longitude(self, data):
        if data.get('latitude') is None and data.get('longitude') is not None:
            # pass
            raise UnprocessableEntity("Latitude and longitude must be of the same type",
                                      {'pointer': '/data/attributes/latitude'})
        if data.get('latitude') is not None and data.get('longitude') is None:
            # pass
            raise UnprocessableEntity("Latitude and longitude must be of the same type",
                                      {'pointer': '/data/attributes/longitude'})

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"

    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    waypoint = fields.Str(allow_none=True)


class MoveDroppedSchema(MoveWithCoordinatesSchema):
    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"


class MoveSeenSchema(MoveWithCoordinatesSchema):

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"


class MoveDippedSchema(MoveWithCoordinatesSchema):

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"


class MoveGrabbedSchema(MoveWithCoordinatesOptionalSchema):

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        strict = True
        dateformat = "%Y-%m-%dT%H:%M:%S"


class MoveCommentSchema(MoveSchema):

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"


class MoveArchiveSchema(MoveSchema):

    class Meta:
        type_ = 'move'
        self_view = 'v1.move_details'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'v1.moves_list'
        inflect = dasherize
        ordered = True
        dateformat = "%Y-%m-%dT%H:%M:%S"
