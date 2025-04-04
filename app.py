from flask import Flask, jsonify, request, render_template
import boto3
import uuid
from boto3.dynamodb.conditions import Key
from datetime import datetime
from auth import token_required
from flask_admin import Admin, BaseView, expose


app = Flask(__name__)
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('form')
dynamodb_for_modify = boto3.client('dynamodb')


class DynamoDBView(BaseView):
    @expose('/')
    def index(self):
        response = table.scan()
        items = response.get('Items', [])
        return self.render('admin/dynamo.html', items=items)


admin = Admin(app, name='Form Admin', template_mode='bootstrap3')
admin.add_view(DynamoDBView(name='Forms', endpoint='forms'))


@app.route('/')
def index():
    return jsonify({"message": "Form API가 실행 중입니다"})


@app.route('/admin-login')
def admin_login():
    return render_template('admin_login.html')


@app.route('/api/forms/', methods=['GET'])
@token_required
def get_forms(current_user):
    search_key = request.args.get('search_key')
    search_value = request.args.get('search_value')

    if search_key and search_value:
        response = table.scan(
            FilterExpression=Key(search_key).begins_with(search_value)
        )
    else:
        response = table.scan()
    return jsonify(response['Items'])


@app.route('/api/forms/', methods=['POST'])
@token_required
def create_form(current_user):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    item = data.copy()
    item["id"] = str(uuid.uuid4())
    try:
        dynamodb_for_modify.transact_write_items(
            TransactItems=[
                {
                    'Put': {
                        'TableName': 'form',
                        'Item': {
                            'item_id': {'N': str(item["item_id"])},
                            'title': {'S': item["title"]},
                            'field_type': {'S': item["field_type"]},
                            'created_at': {'S': datetime.now().isoformat()},
                            'updated_at': {'S': datetime.now().isoformat()}
                        }
                    }
                }
            ]
        )
        return jsonify({"message": "Form created successfully"}), 201
    except Exception as e:
        print(f"트랜잭션 실패: {str(e)}")
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
