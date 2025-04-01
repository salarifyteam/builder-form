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
    table.put_item(Item={
        "item_id": item["item_id"],
        "title": item["title"],
        "response": item["response"],
        "field_type": item["field_type"],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    })
    return jsonify({"message": "Form created successfully"}), 201


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
