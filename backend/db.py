import boto3


def get_service_resource():
    return boto3.resource("dynamodb").Table("service")


def get_dynamodb_client():
    return boto3.client("dynamodb")
