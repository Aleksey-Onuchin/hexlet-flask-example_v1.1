from flask import Flask, request, make_response, render_template, flash, get_flashed_messages, redirect, url_for, session
import json

# Это callable WSGI-приложение
app = Flask(__name__)
app.secret_key = "secret_key"

@app.route('/users/new')
def new_user_form():
    if not 'email' in session:
        return redirect (url_for('login'))
    user = {}
    errors = {}
    return render_template('/users/new.html', user=user, errors=errors, login=session['email'])

@app.post('/users')
def add_new_user():
    if not 'email' in session:
        return redirect (url_for('login'))
    user = request.form.to_dict()
    id = find_max_id()
    user['id'] = id + 1
    errors = validate(user)
    if errors:
        return render_template('/users/new.html', user=user, errors=errors), 422
    users = json.loads(request.cookies.get('users', json.dumps([])))
    users.append(user)
    flash('User was added successfully', 'success')
    encoded_users = json.dumps(users)
    responce = make_response(redirect ('users'))
    responce.set_cookie('users', encoded_users)
    return responce

@app.route('/users')
def show_users():
    if not 'email' in session:
        return redirect (url_for('login'))
    messages = get_flashed_messages(with_categories=True)
    name = request.args.get('name', '')
    result = []
    users = json.loads(request.cookies.get('users', json.dumps([])))
    if not name:
        result = users
    else:
        for user in users:
            if name.lower() in user['name'].lower():
                result.append(user)
    responce = make_response(render_template('users/index.html', name=name, users=result, messages=messages, search=name, login=session['email']))
    encoded_users = json.dumps(users)
    responce.set_cookie('users', encoded_users)
    return responce


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if not request.form['email']:
            return redirect (url_for('login'))
        session['email'] = request.form['email']
        return redirect(url_for('show_users'))
    return render_template('users/login.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('show_users'))


@app.route('/users/<name>')
def show_user(name):
    if not 'email' in session:
        return redirect (url_for('login'))
    users = json.loads(request.cookies.get('users', json.dumps([])))
    for user in users:
        if user['name'] == name:
            responce = make_response(render_template('users/show.html', user=user, login=session['email']))
            encoded_users = json.dumps(users)
            responce.set_cookie('users', encoded_users)
            return responce


@app.route('/users/<id>/edit')
def edit_user(id):
    if not 'email' in session:
        return redirect (url_for('login'))
    errors={}
    users = json.loads(request.cookies.get('users', json.dumps([])))
    for user in users:
        if user['id'] == int(id):
            responce = make_response(render_template('users/edit.html', user=user, errors=errors, login=session['email']))
            encoded_users = json.dumps(users)
            responce.set_cookie('users', encoded_users)
            return responce


@app.post('/users/<id>/patch')
def patch_user(id):
    if not 'email' in session:
        return redirect (url_for('login'))
    users = json.loads(request.cookies.get('users', json.dumps([])))
    others = []
    for user in users:
        if user['id'] == int(id):
            user_to_patch = user
        else:
            others.append(user)
    data = request.form.to_dict()
    errors = validate(data)
    if errors:
        return render_template('/users/edit.html', user=data, errors=errors, login=session['email']), 422
    user_to_patch['name'] = data['name']
    user_to_patch['email'] = data['email']
    others.append(user_to_patch)
    encoded_users = json.dumps(others)
    flash('User data has been updated', 'success')
    responce = make_response(redirect(url_for('show_users')))
    responce.set_cookie('users', encoded_users)
    return responce
    

@app.route('/users/<id>/delete')
def prep_for_deleting(id):
    return render_template('/users/delete.html', id=id, login=session['email'])


@app.post('/users/<id>/delete')
def delete_user(id):
    users = json.loads(request.cookies.get('users', json.dumps([])))
    others = []
    for user in users:
        if user['id'] == int(id):
            user_to_delete = user
        else:
            others.append(user)
    encoded_users = json.dumps(others)
    flash('User was deleted', 'success')
    responce = make_response(redirect(url_for('show_users')))
    responce.set_cookie('users', encoded_users)
    return responce
    

def validate(user):
    errors={}
    if len(user['name']) == 0:
        errors['name'] = "Name field can't be blank"
    elif len(user['name']) < 4:
        errors['name'] = 'Cant be shorter than 4 letters'
    if len(user['email']) == 0:
        errors['email'] = "E-mail field can't be blank"
    elif '.' not in user['email']:
        errors['email'] = 'Must contain domen name'
    return errors

def find_max_id():
    users = json.loads(request.cookies.get('users', json.dumps([])))
    if not users:
        return 0
    res = 0
    for user in users:
        if user['id'] > res:
            res = user['id']
    return res
