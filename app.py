from flask import Flask, render_template, url_for, request, flash, \
    redirect, Response
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from pymysql.cursors import DictCursor
from LoginUser import LoginUser
from flask_login import LoginManager, login_user, current_user,\
    logout_user, login_required
import datetime
import re

app = Flask(__name__)
app.secret_key = ''
login_manager = LoginManager(app)
login_manager.login_view = 'sign_in'
login_manager.login_message = 'Please, sign in!'
login_manager.login_message_category = 'danger'
conn = None
cursor = None


@app.before_request
def before_req():
    global conn
    global cursor
    conn = pymysql.connect(
    )
    cursor = conn.cursor()


@app.teardown_request
def teardownrequst(f):
    conn.close()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('tasks'))
    else:
        return redirect(url_for('sign_in'))


@app.route('/tasks')
@login_required
def tasks():
    cursor.execute('SELECT * FROM lists WHERE id_user=%s ORDER BY id DESC',
                   current_user.get_id())
    lists = cursor.fetchall()
    tasks = {}
    for list in lists:
        cursor.execute('SELECT * FROM tasks WHERE id_list=%s ORDER BY id DESC',
                       list['id'])
        tasks_of_list = cursor.fetchall()
        tasks[list['id']] = tasks_of_list
    return render_template('tasks.html', lists=lists, tasks=tasks)


@app.route('/addlist', methods=['POST'])
@login_required
def add_list():
    cursor.execute('INSERT INTO lists(id_user, name) VALUES (%s,%s)',
                   (current_user.get_id(), request.form['name']))
    conn.commit()
    return redirect(url_for('tasks'))


@app.route('/renamelist', methods=['POST'])
@login_required
def rename_list():
    cursor.execute('UPDATE lists SET name=%s WHERE id=%s',
                   (request.form['name'], request.form['id']))
    conn.commit()
    return redirect(url_for('tasks'))


@app.route('/deletelist/<int:id>')
@login_required
def delete_list(id):
    cursor.execute('DELETE FROM lists WHERE id=%s', id)
    conn.commit()
    cursor.execute('DELETE FROM tasks WHERE id_list=%s', id)
    conn.commit()
    return Response("{'a':'b'}", status=200, mimetype='application/json')


@app.route('/addtask', methods=['POST'])
@login_required
def add_task():
    req_date = request.form['date'].split()
    req_time = req_date[4].split(':')
    res_date = datetime.datetime(int(req_date[3]),
                                 int(getMonth(req_date[1])),
                                 int(req_date[2]),
                                 int(req_time[0]),
                                 int(req_time[1]),
                                 int(req_time[2]))

    cursor.execute('INSERT INTO tasks(id_list, text, deadline) VALUE(%s,%s, %s)',
                   (request.form['list_id'], request.form['tasktext'], res_date))
    conn.commit()
    return Response("{'a':'b'}", status=200, mimetype='application/json')


@app.route('/deletetask', methods=['POST'])
@login_required
def delete_task():
    cursor.execute('DELETE FROM tasks WHERE id_list=%s and text=%s',
                   (request.form['listid'], request.form['tasktext']))
    conn.commit()
    return Response("{'a':'b'}", status=200, mimetype='application/json')


@app.route('/renametask', methods=['POST'])
@login_required
def rename_task():
    res_date = datetime.datetime.strptime(request.form['deadline'], '%Y-%m-%dT%H:%M')
    cursor.execute('UPDATE tasks SET text=%s, deadline=%s WHERE id_list=%s and text=%s',
                   (request.form['name'], res_date, request.form['id'], request.form['oldtext']))
    conn.commit()
    return redirect(url_for('tasks'))


@app.route('/readytask', methods=['POST'])
@login_required
def ready_task():
    cursor.execute('UPDATE tasks SET status=%s WHERE id_list=%s and text=%s',
                   (request.form['status'], request.form['listid'], request.form['tasktext']))
    conn.commit()
    return Response("{'a':'b'}", status=200, mimetype='application/json')


@app.route('/changeprior', methods=['POST'])
@login_required
def change_prior():
    cursor.execute('SELECT id, status FROM tasks WHERE id_list=%s and text=%s',
                   (request.form['id'], request.form['text1']))
    id_text1 = cursor.fetchone()
    cursor.execute('SELECT id, status FROM tasks WHERE id_list=%s and text=%s',
                   (request.form['id'], request.form['text2']))
    id_text2 = cursor.fetchone()
    cursor.execute('UPDATE tasks SET text=%s, status=%s WHERE id=%s',
                   (request.form['text1'], id_text1['status'], id_text2['id']))
    conn.commit()
    cursor.execute('UPDATE tasks SET text=%s, status=%s WHERE id=%s',
                   (request.form['text2'], id_text2['status'], id_text1['id']))
    conn.commit()
    return Response("{'a':'b'}", status=200, mimetype='application/json')


@login_manager.user_loader
def load_user(user_id):
    return LoginUser().fromDB(user_id, cursor)


@app.route('/sign-in', methods=['POST', 'GET'])
def sign_in():
    if current_user.is_authenticated:
        return redirect(url_for('tasks'))
    else:
        if request.method == 'POST':
            cursor.execute('SELECT * FROM users WHERE login=%s',
                           request.form['login'])
            res = cursor.fetchone()
            if res:
                is_pass = check_password_hash(res['password'],
                                              request.form['password'])
                if is_pass:
                    loginUser = LoginUser().create(res)
                    login_user(loginUser, remember=True)
                    return redirect('tasks')
                else:
                    flash('Wrong password or login!', 'danger')
            else:
                flash('Wrong password or login!', 'danger')
    return render_template('sign-in.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('sign_in'))


@app.route('/sign-up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        if current_user.is_authenticated:
            return redirect(url_for('tasks'))
        else:
            if re.match("^[a-zA-Z0-9]{6,25}$", request.form['login']):
                if re.match("^(?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{6,25}$",
                            request.form['password']):
                    cursor.execute('SELECT * FROM users WHERE login=%s', request.form['login'])
                    is_login_required = cursor.fetchall()
                    if is_login_required == ():
                        hash_pass = generate_password_hash(request.form['password'])
                        is_reg = cursor.execute('INSERT INTO users(name,login,password) VALUES(%s,%s,%s)',
                                                (request.form['name'], request.form['login'], hash_pass))
                        conn.commit()
                        if is_reg:
                            flash('Successfuly!', 'success')
                            return redirect(url_for('sign_in'))
                        else:
                            flash('Something wrong!', 'danger')
                    else:
                        flash('Try another login!', 'danger')
                        return redirect(url_for('errorsign_up'))
                else:
                    flash(
                        'Password must contain at least eight characters, at least one number and both lower and uppercase letters and special characters(!@#$%^&*). Minimum 6 and maximum 25 characters.',
                        'danger')
                    return redirect(url_for('errorsign_up'))
            else:
                flash('Login name should contain minimum 6 and maximum 25 characters and only alphanumeric characters are allowed.', 'danger')
                return redirect(url_for('errorsign_up'))
    return render_template('sign-up.html')


@app.route('/errorsignup')
def errorsign_up():
    return redirect(url_for('sign_up'))


@app.errorhandler(Exception)
def handle_error(e):

    return render_template('error.html'), e.code


def getMonth(month):
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return months.index(month) + 1


if __name__ == '__main__':
    app.run(debug=True)
