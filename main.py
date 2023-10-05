from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import InputRequired, NumberRange
from flask_migrate import Migrate

# Create a Flask application instance
app = Flask(__name__)

# Configure the database connection and specify the database file
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///books-collection.db"

# Set a secret key for securely handling forms
app.config["SECRET_KEY"] = "8BYkEfBA6O6donzWlSihBXox7C0sKR6b"

# Initialize Bootstrap for styling
bootstrap = Bootstrap5(app)

# Initialize SQLAlchemy for database operations
db = SQLAlchemy(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)


# Define a model for the 'Book' table in the database
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    author = db.Column(db.String(250), nullable=False)
    review = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f"<Book {self.title}>"


# Define a form class 'FormBooks' for adding/editing books
class FormBooks(FlaskForm):
    book_name = StringField("Book Name", validators=[InputRequired()])
    book_author = StringField("Author", validators=[InputRequired()])
    review = FloatField(
        "Rating, e.g: 9.0", validators=[InputRequired(), NumberRange(min=0, max=10)]
    )
    submit = SubmitField("Submit")


# Define a route for the home page
@app.route("/")
def home():
    # Retrieve all books and order them by the date they were added
    my_books = Book.query.order_by(Book.date_added)
    num_books = my_books.count()
    return render_template("index.html", all_books=my_books, num_books=num_books)


# Define a route for adding books
@app.route("/add", methods=["GET", "POST"])
def add():
    form = FormBooks()
    if request.method == "POST" and form.validate_on_submit():
        # Check if the book already exists based on title and author
        title = form.book_name.data.title()
        author = form.book_author.data.title()
        review = form.review.data

        existing_book = Book.query.filter_by(title=title, author=author).first()

        if existing_book is None:
            # Create a new book record and add it to the database
            book = Book(title=title, author=author, review=review)
            db.session.add(book)
            db.session.commit()

            # Clear the form fields after a book has been successfully added to the library
            form.book_name.data = ""
            form.book_author.data = ""
            form.review.data = ""
        else:
            flash("Book already exists in the library")
            return render_template("add.html", form=form)
        return redirect(url_for("home"))

    return render_template("add.html", form=form)


# Define a route for editing books
@app.route("/edit/<int:book_id>", methods=["GET", "POST"])
def edit(book_id):
    # Fetch the book by its ID from the database
    book = Book.query.get(book_id)

    if book is None:
        # Handle the case where the book with the given ID does not exist
        return "Book not found", 404

    form = FormBooks()

    if request.method == "POST" and form.validate_on_submit():
        # Update the book's details with the form data
        book.title = form.book_name.data.title()
        book.author = form.book_author.data.title()
        book.review = form.review.data

        # Commit the changes to the database
        db.session.commit()

        # Redirect to the home page or wherever you want to go after editing
        return redirect(url_for("home"))

    # Pre-fill the form with the book's current details
    form.book_name.data = book.title
    form.book_author.data = book.author
    form.review.data = book.review

    return render_template("edit.html", form=form, book=book)


# Define a route for deleting books
@app.route("/delete/<int:book_id>")
def delete(book_id):
    book = Book.query.get(book_id)

    if book is None:
        flash("Book not found", "error")
        return redirect(url_for("home"))

    try:
        # Delete the book from the database
        db.session.delete(book)
        db.session.commit()
        flash("Book Removed From Your Library!", "success")
        return redirect(url_for("home"))

    except SQLAlchemyError:
        # Rollback changes in case of an error
        db.session.rollback()
        flash("An Error Occurred!", "error")
        return redirect(url_for("home"))


# Run the Flask application
if __name__ == "__main__":
    with app.app_context():
        # Create the database tables
        db.create_all()
    app.run(debug=True)
