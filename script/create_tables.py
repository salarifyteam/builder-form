import boto3


def create_service_table():
    dynamodb = boto3.client(
        "dynamodb",
        endpoint_url="http://localhost:8000",
        region_name="ap-northeast-2",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )

    try:
        table = dynamodb.create_table(
            TableName="service",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},  # Partition key
                {"AttributeName": "SK", "KeyType": "RANGE"},  # Sort key
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                    "ProvisionedThroughput": {
                        "ReadCapacityUnits": 5,
                        "WriteCapacityUnits": 5,
                    },
                }
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5,
            },
        )
        print("Table created successfully!")
        return table
    except dynamodb.exceptions.ResourceInUseException:
        print("Table already exists!")
    except Exception as e:
        print(f"Error creating table: {str(e)}")


if __name__ == "__main__":
    create_service_table()
