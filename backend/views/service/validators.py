from marshmallow import Schema, fields
from marshmallow.validate import OneOf


class ServiceSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(required=True)


class FormSchema(Schema):
    fieldTitle = fields.String(required=True)
    fieldDescription = fields.String(required=True)
    fieldCategory = fields.String(required=True, validate=OneOf(["TEXT"]))
    fieldType = fields.String(required=True, validate=OneOf(["SHORT", "LONG"]))
    fieldDataType = fields.String(
        required=True, validate=OneOf(["NUM", "TEXT"])
    )
    fieldRequired = fields.Boolean(required=True)
    fieldNumber = fields.Integer(required=True)


class ServiceWithFormSchema(Schema):
    companyId = fields.Integer(required=True)
    service = fields.Nested(ServiceSchema)
    form = fields.List(fields.Nested(FormSchema))
