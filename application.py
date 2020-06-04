import os

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import *
from werkzeug.security import generate_password_hash, check_password_hash

import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

books = book_list()

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template("index.html", books=books)
    else:
        search = request.form.get("query")
        if not search:
            return "TODO ERROR NO QUERY PROVIDED"
        query = "%" + search + "%"
        query = query.title()
        queried_books = queried_book_list(query)
        return render_template("results.html", queried_books=queried_books)

@app.route("/book/<isbn>", methods=["GET", "POST"])
@login_required
def book(isbn):
    if request.method == "GET":
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn': isbn})
        book_info = book.fetchall()
        for i in book_info:
            isbn = i.isbn
            title = i.title
            author = i.author
            year = i.year
        reviews = db.execute("SELECT username, review, time_posted, rating FROM reviews WHERE isbn = :isbn", 
                                {"isbn": isbn}).fetchall()
        
        # grab stuff from goodreads api

        response = requests.get("https://www.goodreads.com/book/review_counts.json",
                    params={"key": "jgCbhxblCv87EvyAXzAm2Q", "isbns": isbn})
        good_reads = response.json()['books'][0]
        average_rating = good_reads['average_rating']
        total_ratings = good_reads['ratings_count']

        return render_template("book.html",
                                    isbn=isbn,
                                    title=title, 
                                    author=author, 
                                    year=year, 
                                    reviews=reviews, 
                                    average_rating=average_rating, 
                                    total_ratings=total_ratings)
    if request.method == "POST":
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})
        book_info = book.fetchall()
        for i in book_info:
            isbn = i.isbn
            title = i.title
            author = i.author
            year = i.year
        review = request.form.get("review")
        rating = request.form.get("rating")
        username = session['username']
        db.execute("INSERT INTO reviews VALUES (:isbn, :username, :review, :rating)",
                    {"isbn": isbn, "username": username, "review": review, "rating": rating})
        db.commit()
        
        reviews = db.execute("SELECT username, review, rating, time_posted FROM reviews WHERE isbn = :isbn",
                                 {"isbn": isbn}).fetchall()
        
        return render_template("book.html", isbn=isbn, title=title, author=author, year=year, reviews=reviews)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        if not username:
            return "TODO ERROR MESSAGE USERNAME"
        password = request.form.get("password")
        if not password:
            return "TODO ERROR PASSWORD"
        confirm = request.form.get("confirmation")
        if password != confirm:
            return "TODO ERROR PASSWORDS DID NOT MATCH"
        pw_hash = generate_password_hash(password)
        db.execute("INSERT INTO users (username, pw_hash) VALUES (:username, :password)",
                        {"username": username, "password": pw_hash})
        db.commit()
        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    # forget any user_id
    session.clear()

    if request.method == "POST":
        # ensure username is submitted
        username = request.form.get("username")
        if not username:
            return "TODO ERROR NO USERNAME"

        # ensure pw is submitted
        password = request.form.get("password")
        if not password:
            return "TODO ERROR NO PASSWORD"

        # query database for username
        username_check = db.execute("SELECT * FROM users WHERE username = :username",
                                        {"username": username}).fetchall()

        for i in username_check:
            pw_hash = i.pw_hash
            user_id = i.user_id

        if len(username_check) != 1 or not check_password_hash(pw_hash, password):
            return "TODO ERROR INVALID USERNAME OR PASSWORD"

        # Remember which user has logged in
        session["username"] = username

        return redirect("/")
    
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/api/capribooks/<isbn>")
def books_api(isbn):
    reviews = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn})

    reviews = reviews.fetchall()

    if reviews == []:
        return jsonify({"error": "Book not in our database"}), 422

    for i in reviews:
        return jsonify({
            "isbn": i.isbn,
            "title": i.title,
            "author": i.author,
            "publication_year": i.year
        })