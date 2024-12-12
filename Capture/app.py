from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Make sure this is set for sessions to work
db = SQLAlchemy(app)

# User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# Note model (added user_id for note-owner relation)
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Store HTML content
    tags = db.Column(db.String(100), nullable=True)
    is_saved = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to link notes to users

    user = db.relationship('User', backref=db.backref('notes', lazy=True))

# Routes for User Registration and Login
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username already exists!", 'danger')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new user and add to the database
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully!", 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        flash("You are already logged in.", 'info')  # Flash message if already logged in
        return redirect(url_for('home'))  # If already logged in, redirect to home

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Find the user in the database
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):  # user.password is already bytes
            session['user_id'] = user.id  # Store user session
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
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')  # Default to 'title' if not provided

    # Searching for notes on the homepage (only user-specific notes)
    if query:
        if search_type == 'title':
            notes = Note.query.filter(Note.title.ilike(f'%{query}%'), Note.user_id == session['user_id']).all()
        else:
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%'), Note.user_id == session['user_id']).all()
    else:
        notes = Note.query.filter_by(is_saved=False, user_id=session['user_id']).all()  # Only unsaved notes by user

    return render_template('home.html', notes=notes)

@app.route('/saved')
def saved_notes():
    if 'user_id' not in session:
        flash("You need to login first!", 'warning')
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')  # Default to 'title' if not provided

    # Searching only within saved notes for the logged-in user
    if query:
        if search_type == 'title':
            notes = Note.query.filter(Note.title.ilike(f'%{query}%'), Note.is_saved == True, Note.user_id == session['user_id']).all()
        else:
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%'), Note.is_saved == True, Note.user_id == session['user_id']).all()
    else:
        notes = Note.query.filter_by(is_saved=True, user_id=session['user_id']).all()  # Show only saved notes for the user

    return render_template('saved_notes.html', notes=notes)

@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']  # This will be the HTML content from Quill
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
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    note = Note.query.get_or_404(id)

    # Ensure the note belongs to the current user
    if note.user_id != session['user_id']:
        flash('You cannot edit someone else\'s note.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']  # Get the HTML content from Quill
        note.tags = request.form['tags']
        db.session.commit()
        flash('Note updated successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('edit_note.html', note=note)

@app.route('/notes/delete/<int:id>')
def delete_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    note = Note.query.get_or_404(id)

    # Ensure the note belongs to the current user
    if note.user_id != session['user_id']:
        flash('You cannot delete someone else\'s note.', 'danger')
        return redirect(url_for('home'))

    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/notes/save/<int:id>')
def save_note(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    note = Note.query.get_or_404(id)
    note.is_saved = True  # Mark the note as saved
    db.session.commit()
    flash('Note saved successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session
    flash("Logged out successfully!", 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    db.create_all()  # Ensure that the database is created and schema is updated
    app.run(debug=True)
