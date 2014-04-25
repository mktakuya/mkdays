#!/usr/bin/env python
# coding:utf-8
from __future__ import with_statement
from contextlib import closing
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
        abort, render_template, flash
import settings

app = Flask(__name__)
app.config.from_object(settings)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.after_request
def after_request(response):
    g.db.close()
    return response

@app.route('/')
def show_entries():
    cur = g.db.execute('select id, title, text from entries order by id desc')
    entries = [dict(entry_id=row[0], title=row[1], text=row[2]) for row in cur.fetchall()][:3]
    return render_template('show_entries.html', entries=entries)

@app.route('/entries/<int:entry_id>')
def show_detail(entry_id):
    cur = g.db.execute("select id, title, text from entries where id=?", str(entry_id))
    row = cur.fetchone()
    entry = dict(entry_id=row[0], title=row[1], text=row[2])
    return render_template('show_detail.html', entry=entry)

@app.route('/entries/<int:entry_id>/edit')
def edit_entry(entry_id):
    cur = g.db.execute("select id, title, text from entries where id=?", str(entry_id))
    row = cur.fetchone()
    entry = dict(entry_id=row[0], title=row[1], text=row[2])
    return render_template('edit_entry.html', entry=entry)

@app.route('/entries/<int:entry_id>/update', methods=['POST'])
def update_entry(entry_id):
    if request.method == 'POST':
        cur = g.db.execute("update entries set title = ?, text = ? where id = ?",
                (request.form['title'], request.form['text'], entry_id))
        g.db.commit()
        flash('Entry was successfully edited')
        return redirect(url_for('show_entries'))
    else:
        return redirect(url_for('show_entries'))

@app.route('/entries/<int:entry_id>/delete')
def delete_entry(entry_id):
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('delete from entries where id=?', str(entry_id))
    g.db.commit()
    flash('Entry was successfully deleted')
    return redirect(url_for('show_entries'))
    

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))

if __name__ == '__main__':
    app.run()

