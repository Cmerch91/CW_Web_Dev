from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db = SQLAlchemy(app)

# Database model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Store HTML content
    tags = db.Column(db.String(100), nullable=True)
    is_saved = db.Column(db.Boolean, default=False)  # Column to track saved notes

# Routes
@app.route('/')
def home():
    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')  # Default to 'title' if not provided

    # Searching for notes on the homepage
    if query:
        if search_type == 'title':
            # Search both saved and unsaved notes by title
            notes = Note.query.filter(Note.title.ilike(f'%{query}%')).all()
        else:
            # Search both saved and unsaved notes by tags
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%')).all()
    else:
        # Show only unsaved notes by default if there's no search query
        notes = Note.query.filter_by(is_saved=False).all()

    return render_template('home.html', notes=notes)

@app.route('/saved')
def saved_notes():
    query = request.args.get('query')
    search_type = request.args.get('search_type', 'title')  # Default to 'title' if not provided

    # Searching only within saved notes
    if query:
        if search_type == 'title':
            notes = Note.query.filter(Note.title.ilike(f'%{query}%'), Note.is_saved == True).all()
        else:
            notes = Note.query.filter(Note.tags.ilike(f'%{query}%'), Note.is_saved == True).all()
    else:
        notes = Note.query.filter_by(is_saved=True).all()  # Show only saved notes

    return render_template('saved_notes.html', notes=notes)

@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']  # This will be the HTML content from Quill
        tags = request.form['tags']
        new_note = Note(title=title, content=content, tags=tags)
        db.session.add(new_note)
        db.session.commit()
        flash('Note created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('note.html')


@app.route('/notes/<int:id>', methods=['GET', 'POST'])
def edit_note(id):
    note = Note.query.get_or_404(id)
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
    note = Note.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('home'))

@app.route('/notes/save/<int:id>')
def save_note(id):
    note = Note.query.get_or_404(id)
    note.is_saved = True  # Mark the note as saved
    db.session.commit()
    flash('Note saved successfully!', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    db.create_all()  # Ensure that the database is created and schema is updated
    app.run(debug=True)
