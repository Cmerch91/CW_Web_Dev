from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)
#Creates DB
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(100), nullable=True)
    is_saved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('notes', lazy=True))

#Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!", 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully!", 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

#Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash("You are already logged in.", 'info')
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", 'success')
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password.", 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/')
def home():
    if 'user_id' not in session:
        flash("You need to login first!", 'warning')
        return redirect(url_for('login'))

    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')

    if query:
        if search_type == 'title':
            notes = Note.query.filter(Note.title.ilike(f'%{query}%'), Note.user_id == session['user_id']).all()
        else:
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%'), Note.user_id == session['user_id']).all()
    else:
        notes = Note.query.filter_by(is_saved=False, user_id=session['user_id']).all()

    return render_template('home.html', notes=notes)

#Saved route
@app.route('/saved')
def saved_notes():
    if 'user_id' not in session:
        flash("You need to login first!", 'warning')
        return redirect(url_for('login'))

    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')

#Searches only saved notes
    if query:
        if search_type == 'title':
            notes = Note.query.filter(Note.title.ilike(f'%{query}%'), Note.is_saved == True, Note.user_id == session['user_id']).all()
        else:
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%'), Note.is_saved == True, Note.user_id == session['user_id']).all()
    else:
        notes = Note.query.filter_by(is_saved=True, user_id=session['user_id']).all()

    return render_template('saved_notes.html', notes=notes)

#New note route
@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        new_note = Note(title=title, content=content, tags=tags, user_id=session['user_id'])
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('note.html')

@app.route('/notes/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login')) #redirects if not logged in

    note = Note.query.get_or_404(id)

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        note.tags = request.form['tags']
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('edit_note.html', note=note)

@app.route('/notes/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    note = Note.query.get_or_404(id)

    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/notes/save/<int:id>')
def save_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    note = Note.query.get_or_404(id)
    note.is_saved = True #Marks the note as saved
    db.session.commit()
    flash('Note saved successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user_id', None) #Logs out
    session.pop('username', None) #Removes username from page
    flash("Logged out successfully!", 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
