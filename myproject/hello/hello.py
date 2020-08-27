from flask import Flask, url_for
from markupsafe import escape
from flask import render_template, request, redirect
from flask_mysqldb import MySQL
from datetime import datetime
import time
from flask_mail import Mail, Message 
from flask_http_response import success, result, error
import yaml
app = Flask(__name__)

# database configure
db = yaml.safe_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

# mail configure
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'xxxx'
app.config['MAIL_PASSWORD'] = db['mail_password']


mysql = MySQL(app)
mail = Mail(app)


@app.route('/')
def index():
    return "This is Homepage!, type admin within the url to go to the admin page"

@app.route('/get_interview_slots', methods = ['POST', 'GET'])
def getSlots():
    cur = mysql.connection.cursor()
    result = cur.execute("select * from interview_slots")
    if result == 0:
        arr = []
        cur = {
            "intervieweeName": "NA",
            "interviewerName": "NA",
            "start_time": "NA",
            "end_time": "NA",
            "save_start_time": "NA",
            "save_end_time": "NA",
            "save_interviewee_id": "NA",
            "save_interviewer_id": "NA",
            "flag":1
        }
        arr.append(cur)
        return success.return_response(arr, status=200)

    all_slots = cur.fetchall()
    interviewee_name = []
    interviewer_name = []

    for slot in all_slots:
        cur.execute(f'select name from users where id = {slot[0]}')
        value = cur.fetchall()
        interviewee_name.append(value)
        cur.execute(f'select name from users where id = {slot[1]}')
        value = cur.fetchall()
        interviewer_name.append(value)

    a = list(all_slots)
    b = list(interviewee_name)
    c = list(interviewer_name)
    final = []
    for i in range(0, len(a)):
        name1 = b[i][0][0]
        name2 = c[i][0][0]
        st_time = a[i][2]
        en_time = a[i][3]
        start_time = datetime.strptime(st_time, '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(en_time, '%Y-%m-%dT%H:%M')
        cur = {
            "intervieweeName": name1,
            "interviewerName": name2,
            "start_time": start_time,
            "end_time": end_time,
            "save_start_time": st_time,
            "save_end_time": en_time,
            "save_interviewee_id": a[i][0],
            "save_interviewer_id": a[i][1],
            "flag":0
        }
        final.append(cur)
    return success.return_response(final, status=200)

@app.route('/edit', methods = ['POST', 'GET'])
def edit():
    cur = mysql.connection.cursor()
    details = request.form
    interviewee_id = details['interviewee_id']
    interviewer_id = details['interviewer_id']
    start_time = details['start_time']
    end_time = details['end_time']
    cur.execute(f'delete from interview_slots where interviewee_id = {interviewee_id} and interviewer_id = {interviewer_id} and start_time = "{start_time}" and end_time = "{end_time}"')
    mysql.connection.commit()
    return success.return_response(message='Successfully Completed', status=200)

@app.route('/admin', methods = ['POST', 'GET'])
def admin():
    cur = mysql.connection.cursor()
    
    result = cur.execute("select * from interview_slots")    
    interview_slots = cur.fetchall()

    cur.execute("select * from users")
    userDetails = cur.fetchall()
    interviewee_name = []
    interviewer_name = []
    for slot in interview_slots:
        cur.execute(f'select name from users where id = {slot[0]}')
        cur_interviewee_name = cur.fetchall()
        interviewee_name.append(cur_interviewee_name)
    
    for slot in interview_slots:
        cur.execute(f'select name from users where id = {slot[1]}')
        cur_interviewer_name = cur.fetchall()
        interviewer_name.append(cur_interviewer_name)
   
    if request.method == 'POST':
        interview_details = request.form
        
        interviewee_id = interview_details['interviewee_id']
        interviewer_id = interview_details['interviewer_id']
        start_time = interview_details['start_time']
        end_time = interview_details['end_time']
        cur.execute(f'select start_time, end_time from interview_slots where interviewee_id = {interviewee_id} or interviewer_id = {interviewer_id}')
        booked_slots = cur.fetchall()

        check_start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
        check_end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
        flag = 0
        cur_time = datetime.now()
        s = str(cur_time)
        cur_time = datetime.strptime(s, '%Y-%m-%d %H:%M:%S.%f')
        
        store = (check_end_time - check_start_time)
        tt = (store.seconds / 60)
        if (tt < 30 or tt > 120):
            flag = 1
        print("flag", flag)
        if (check_end_time < check_start_time or check_start_time < cur_time):
            flag = 1
        for slots in booked_slots:
            st_time = slots[0]
            en_time = slots[1]
            st_time = datetime.strptime(st_time, '%Y-%m-%dT%H:%M')
            en_time = datetime.strptime(en_time, '%Y-%m-%dT%H:%M')
            if (check_end_time <= st_time or check_start_time >= en_time):
                continue
            else:
                 flag = 1
        
        if flag == 0:
            cur.execute(f'insert into interview_slots values({interviewee_id}, {interviewer_id}, "{start_time}", "{end_time}")')
            mysql.connection.commit()
            cur.execute(f'select email from users where id = {interviewee_id}')
            recipient1 = cur.fetchall()
            cur.execute(f'select email from users where id = {interviewer_id}')
            recipient2 = cur.fetchall()
            l = []
            l.append(recipient1[0][0])
            l.append(recipient2[0][0])
            #msg = Message(f'Your interview have been schedule from {check_start_time} to {check_end_time}', sender= 'xxxx', recipients= l)
            #mail.send(msg)
            
            return success.return_response(message='Successfully Completed', status=200)
        return success.return_response(message='not possible', status=200)
    return render_template('admin.html', userDetails = userDetails)

if __name__ == "__main__":
    app.run(debug=True)