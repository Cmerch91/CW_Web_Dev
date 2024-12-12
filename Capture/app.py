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
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(100), nullable=True)

# Routes
@app.route('/')
def home():
    # Get the search tag query from the request arguments
    tag = request.args.get('tag')
    if tag:
        # Filter notes where tags contain the search term (case-insensitive)
        notes = Note.query.filter(Note.tags.ilike(f'%{tag}%')).all()
    else:
        # If no search term is provided, display all notes
        notes = Note.query.all()
    return render_template('home.html', notes=notes)

@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
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
        note.content = request.form['content']
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

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
