from flask import Flask, render_template, request, jsonify
import os
import json
from database_utils import create_database_engine
from data_loader import load_and_clean_data, table_mapping, transform_mapping
from sqlalchemy import text, select, func, column
from sqlalchemy.sql import table
from sqlalchemy.sql.expression import select, column
from sqlalchemy.sql import table, column, join

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
DATA_FOLDER = 'static/data'
ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db_path = "my_database.db"
db_engine = create_database_engine(db_path)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template('base.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
         return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = file.filename

        # Ensure the upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

         # Process the uploaded file (e.g., update the JSON data)
        try:
            load_and_clean_data(file_path, db_engine, table_mapping, transform_mapping)
        except Exception as e:
            print(f"Error when loading and cleaning: {e}")
            return jsonify({'error': f'File upload failed: {e}'}), 500
        return jsonify({'message': 'File uploaded successfully', 'reload_required': True}), 200
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/get_data')
def get_data():
    section = request.args.get('section')
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=10, type=int)
    if not section:
        return jsonify({'error': 'Section is required'}), 400

    try:
        with db_engine.connect() as conn:
            if section == 'chats':
                 cm = table("chat_messages").alias("cm")
                 c = table("contacts").alias("c")
                 base_query = select(
                     cm.c.messenger,
                     cm.c.time,
                     cm.c.sender,
                     cm.c.text,
                     c.c.name.label("contact_name")
                    ).select_from(
                         join(cm, c, cm.c.contact_id == c.c.contact_id, isouter=True)
                    )

                 total_count = conn.execute(select(func.count()).select_from(text("chat_messages"))).scalar()
                 result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
                 data = []
                 for row in result:
                     data.append({
                        'messenger': row[0],
                        'time': row[1],
                        'name': row[2] if row[2] else "Unknown",
                        'last_message': row[3],
                        'profile_pic': '/static/images/user.png',
                        'messages': [{'sender': row[2] if row[2] else "Unknown", 'content': row[3]}]
                    })
                # Group messages by sender
                 grouped_data = {}
                 for item in data:
                     key = item['name']
                     if key not in grouped_data:
                         grouped_data[key] = {
                             'name': item['name'],
                            'profile_pic': item['profile_pic'],
                            'last_message': item['last_message'],
                             'messages': item['messages']
                         }
                     else:
                         grouped_data[key]['messages'].extend(item['messages'])
                         grouped_data[key]['last_message'] = item['last_message']
                 data = list(grouped_data.values())

            elif section == 'calls':
                 c = table("calls").alias("c")
                 l = table("locations").alias("l")
                 con = table("contacts").alias("con")
                 base_query = select(
                    c.c.call_type,
                    c.c.time,
                    c.c.from_to,
                    c.c.duration,
                    l.c.location_text,
                    con.c.name.label("contact_name")
                ).select_from(
                     join(c, l, c.c.location_id == l.c.location_id, isouter=True).\
                     join(c, con, c.c.contact_id == con.c.contact_id, isouter=True)
                )

                 total_count = conn.execute(select(func.count()).select_from(text("calls"))).scalar()
                 result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
                 data = [{
                    'call_type': row[0],
                    'time': row[1],
                    'name': row[2] if row[2] else "Unknown",
                    'duration': row[3],
                    'location': row[4] if row[4] else "Unknown",
                    'profile_pic': '/static/images/user.png'
                 } for row in result]
            elif section == 'keylogs':
                 base_query = select(
                    column("application"),
                    column("time"),
                    column("text")
                 ).select_from(table("keylogs"))
                 total_count = conn.execute(select(func.count()).select_from(text("keylogs"))).scalar()
                 result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
                 data = [{'application': row[0], 'time': row[1], 'text': row[2]} for row in result]
            elif section == 'contacts':
                base_query = select(
                    column("name"),
                    column("phone_number"),
                    column("email_id")
                ).select_from(table("contacts"))
                total_count = conn.execute(select(func.count()).select_from(text("contacts"))).scalar()
                result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
                data = [{
                     'name': row[0],
                    'phone_number': row[1],
                    'email_id': row[2],
                     'profile_pic': '/static/images/user.png'
                } for row in result]
            elif section == 'sms':
                 sms = table("sms_messages").alias("sms")
                 l = table("locations").alias("l")
                 con = table("contacts").alias("con")

                 base_query = select(
                     sms.c.sms_type,
                     sms.c.time,
                     sms.c.from_to,
                     sms.c.text,
                     l.c.location_text,
                    con.c.name.label("contact_name")
                ).select_from(
                     join(sms, l, sms.c.location_id == l.c.location_id, isouter=True).\
                     join(sms, con, sms.c.contact_id == con.c.contact_id, isouter=True)
                )
                 total_count = conn.execute(select(func.count()).select_from(text("sms_messages"))).scalar()
                 result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
                 data = []
                 for row in result:
                     data.append({
                       'sms_type': row[0],
                        'time': row[1],
                        'name': row[2] if row[2] else "Unknown",
                       'last_message': row[3],
                        'location': row[4] if row[4] else "Unknown",
                        'profile_pic': '/static/images/user.png',
                       'messages': [{'sender': row[2] if row[2] else "Unknown", 'content': row[3]}]
                    })
                 # Group messages by sender
                 grouped_data = {}
                 for item in data:
                     key = item['name']
                     if key not in grouped_data:
                         grouped_data[key] = {
                             'name': item['name'],
                             'profile_pic': item['profile_pic'],
                            'last_message': item['last_message'],
                             'messages': item['messages']
                         }
                     else:
                         grouped_data[key]['messages'].extend(item['messages'])
                         grouped_data[key]['last_message'] = item['last_message']
                 data = list(grouped_data.values())

            elif section == 'installed_apps':
               base_query = select(
                   column("application_name"),
                    column("package_name"),
                   column("installed_date")
                ).select_from(table("installedapps"))
               total_count = conn.execute(select(func.count()).select_from(text("installedapps"))).scalar()
               result = conn.execute(base_query.limit(per_page).offset((page - 1) * per_page)).fetchall()
               data = [{
                     'name': row[0],
                    'package_name': row[1],
                     'installed_date': row[2],
                    'icon': '/static/images/app_icon.png',
                    'version': '1.0'
                 } for row in result]
            else:
                return jsonify({'error': 'Invalid section'}), 400
        return jsonify({
            'data': data,
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': (total_count + per_page - 1) // per_page
        })
    except Exception as e:
        print(f"Error in get_data: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)