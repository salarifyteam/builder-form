from marshmallow import Schema, fields
from marshmallow.validate import OneOf


class FormSchema(Schema):
    fieldId = fields.String(required=True)
    fieldTitle = fields.String(required=True)
    fieldDescription = fields.String(required=True)
    fieldCategory = fields.String(required=True, validate=OneOf(["TEXT"]))
    fieldType = fields.String(required=True, validate=OneOf(["SHORT", "LONG"]))
    fieldDataType = fields.String(
        required=True, validate=OneOf(["NUM", "TEXT"])
    )
    fieldRequired = fields.Boolean(required=True)
    fieldNumber = fields.Integer(required=True)
    fieldValue = fields.String(required=True)


class ApplicationSchema(Schema):
    name = fields.String(required=True)
    phoneNumber = fields.String(required=True)
    fieldData = fields.List(fields.Nested(FormSchema))
