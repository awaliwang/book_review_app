import os
from functools import wraps

from flask import redirect, session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def book_list():
    books = db.execute("SELECT * FROM books")
    book_list = []
    for i in books:
        isbn = i.isbn
        title = i.title
        author = i.author
        year = i.year
        book = {
            'isbn': isbn,
            'title': title,
            'author': author,
            'year': year
        }
        book_list.append(book)
    return book_list

def queried_book_list(input):
    query = db.execute("SELECT * FROM books WHERE \
                            isbn LIKE :input OR \
                            title LIKE :input OR \
                            author LIKE :input OR \
                            year LIKE :input LIMIT 15", {"input": input})
    
    if query.rowcount == 0:
        return "no book"
    
    queried_list = []
    for i in query:
        isbn = i.isbn
        title = i.title
        author = i.author
        year = i.year
        book = {
            'isbn': isbn,
            'title': title,
            'author': author,
            'year': year
        }
        queried_list.append(book)
    
    return queried_list