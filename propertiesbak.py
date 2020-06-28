# Goodbooks app

import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, func, bindparam, text
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from datetime import datetime, date

from helpers import login_required
import requests
import json
import re

# Configure application
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['JSON_SORT_KEYS'] = False

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    """Show root"""
    return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure user_email was submitted
        if not request.form.get("user_email"):
            return render_template("login.html", error_message="must provide your login email address, 403")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error_message="must provide password, 403")

        # Query database for user_email
        user_email = request.form.get("user_email")
        rows = db.execute(
            "SELECT * FROM users WHERE user_email = :user_email", {"user_email": user_email}).fetchall()

        # Ensure user_email exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["user_hash"], request.form.get("password")):
            return render_template("login.html", error_message="Invalid user email and/or password, 403")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return render_template("search_book.html", success_message="user is logged in")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user password user"""
    uid = int(session["user_id"])

    # User reached route via POS:T (as by submitting a form via POST)
    if request.method == "POST":
        # Query database for user email
        # Ensure old password was submitted
        if not request.form.get("old_password"):
            return render_template("change_password.html", error_message="must provide old password, 403")

        # Ensure password was submitted
        elif not request.form.get("new_password"):
            return render_template("change_password.html", error_message="must provide a new password, 403")

        # Ensure Confirm_password was submitted
        elif not request.form.get("confirm_new_password"):
            return render_template("change_password.html", error_message="must provide confirmation password, 403")

        # Ensure password and confirmation password match
        elif (request.form.get("confirm_new_password") != request.form.get("new_password")):
            return render_template("change_password.html", error_message="Password and confirmation password don't match, 403")

        rows = db.execute("SELECT id, user_email, user_hash FROM users WHERE id = :user_id", {
                          "user_id": uid}).fetchall()
        for row in rows:
            if row['id'] == uid:
                old_hash = row['user_hash']
                user_email = row['user_email']

        # check old password hash key
        if not check_password_hash(old_hash, request.form.get("old_password")):
            return render_template("change_password.html", error_message="Must provide correct old password, 403")

        new_hash = generate_password_hash(request.form.get("new_password"))

        update_hash_qry = """
                UPDATE users SET user_hash = :user_hash WHERE id = :uid
             """
        params = {'uid': uid, "user_hash": new_hash}

        db.execute(text(update_hash_qry), params)

        db.commit()

        session.clear()

        return render_template("login.html")

    else:
        return render_template("change_password.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # Query database for user email
    # execute this SQL command and return for flight in flights
    users = db.execute("SELECT user_email FROM users").fetchall()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure first name was submitted
        if not request.form.get("user_firstname"):
            return render_template("register.html", error_message="must provide your First Name, 403")

        # Ensure last name was submitted
        elif not request.form.get("user_lastname"):
            return render_template("register.html", error_message="must provide your last name, 403")

        # Ensure email was submitted
        elif not request.form.get("user_email"):
            return render_template("register.html", error_message="must provide your email address, 403")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("register.html", error_message="must provide password, 403")

        # Ensure Confirm_password was submitted
        elif not request.form.get("confirm_password"):
            return render_template("register.html", error_message="must provide confirmation password, 403")

        elif (request.form.get("confirm_password") != request.form.get("password")):
            return render_template("register.html", error_message="Password and confirmation password don't match, 403")

        # Check if user_email exists in database
        for user in users:
            if (user['user_email'].lower() == request.form.get("user_email").lower()):
                return render_template("register.html", error_message="This email address already exists, 403")

        # generate password hash key
        user_fn = request.form.get("user_firstname").capitalize()
        user_ln = request.form.get("user_lastname").capitalize()
        user_email = request.form.get("user_email").lower()
        user_hash = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (user_firstname, user_lastname, user_email, user_hash) VALUES (:user_firstname, :user_lastname, :user_email, :user_hash)",
                   {"user_firstname": user_fn, "user_lastname": user_ln, "user_email": user_email, "user_hash": user_hash})
        db.commit()
        return render_template("login.html", success_message="You've signed up for our service with success")

    else:
        return render_template("register.html")


@ app.route("/add_property", methods=["GET", "POST"])
@ login_required
def add_property():
    """Search for books"""

    # User reached route via POST (as by submitting a form via POST)
    # search for ISBN, AUTHOR ou TITLE based on entry
    if request.method == "POST":

        # Ensure user_email was submitted
        if not (request.form.get("prop_name") or request.form.get("prop_address") or request.form.get("prop_purchase_price") or request.form.get("prop_purchase_date") or request.form.get("prop_zip") or request.form.get("prop_city"):
            return render_template("add_property.html", error_message="Please enter all requested information, 403")

        search_book = request.form.get("search_book")
        books = db.execute("SELECT * FROM books WHERE isbn LIKE :search_book OR lower(title) LIKE :search_book OR lower(author) LIKE :search_book ORDER BY title ASC ",
                           {"search_book": "%" + search_book.lower() + "%"}).fetchall()

        if not books:
            return render_template("add_property.html", error_message="No book matches this search")

        return render_template("index.html")

    else:
        return render_template("add_property.html")


@ app.route("/show_page/<string:isbn_page>", methods=["GET", "POST"])
@ login_required
def show_page(isbn_page):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn_page ",
                      {"isbn_page": isbn_page}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :isbn_page ",
                         {"isbn_page": isbn_page}).fetchall()
    """ Show book details + add new review """

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "OCzrG88Hujx2LRMl0UyX2w", "isbns": isbn_page})
    if not res.status_code != 200:

        gr_review = res.json()

        gr_ratings = {}
        gr_ratings['average_score'] = gr_review['books'][0]["average_rating"]
        gr_ratings['reviews_count'] = gr_review['books'][0]["reviews_count"]

    return render_template("show_page.html", book=book, reviews=reviews, gr_ratings=gr_ratings)


@ app.route("/new_review/<string:review_isbn>", methods=["GET", "POST"])
@ login_required
def new_review(review_isbn):

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "OCzrG88Hujx2LRMl0UyX2w", "isbns": review_isbn})
    if not res.status_code != 200:

        gr_review = res.json()

        gr_ratings = {}
        gr_ratings['average_score'] = gr_review['books'][0]["average_rating"]
        gr_ratings['reviews_count'] = gr_review['books'][0]["reviews_count"]

    if request.method == "GET":
        return render_template("new_review.html", review_isbn=review_isbn, gr_ratings=gr_ratings)
    else:
        rtext = request.form.get("review_text")
        rr = request.form.get("review_rating")
        now = datetime.now()
        rd = now.strftime("%d/%m/%Y")
        rt = now.strftime("%H:%M:%S")
        userid = session["user_id"]

        review_user_email = db.execute(
            "SELECT user_email FROM users WHERE id = :id ", {"id": userid}).fetchone()
        ru = review_user_email['user_email']

        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": "OCzrG88Hujx2LRMl0UyX2w", "isbns": review_isbn})

        actual_book = db.execute("SELECT * FROM books WHERE isbn = :book_isbn ",
                                 {"book_isbn": review_isbn}).fetchone()

        review_exist = db.execute("SELECT * FROM reviews WHERE book_id = :review_isbn AND user_id = :userid ", {
                                  "review_isbn": review_isbn, "userid": userid}).fetchall()

        if not review_exist:
            db.execute("INSERT INTO reviews (book_id, user_id, review_text, review_rating, review_date, review_time, review_user_email) VALUES (:book_id, :user_id, :review_text, :review_rating, :review_date, :review_time, :review_user_email)", {
                       "book_id": review_isbn, "user_id": userid, "review_text": rtext, "review_rating": rr, "review_date": rd, "review_time": rt, "review_user_email": ru})
            db.commit()

            reviews = db.execute("SELECT * FROM reviews WHERE book_id = :review_isbn ",
                                 {"review_isbn": review_isbn}).fetchall()

            return render_template("show_page.html", book=actual_book, reviews=reviews, gr_ratings=gr_ratings)

        else:
            reviews = db.execute("SELECT * FROM reviews WHERE book_id = :review_isbn ",
                                 {"review_isbn": review_isbn}).fetchall()
            return render_template("show_page.html", book=actual_book, reviews=reviews, gr_ratings=gr_ratings, error_message="This user has already added a review for this book")


@ app.route("/API/<string:isbn>")
@ login_required
def API(isbn):
    """API details about a book based on isbn."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                      {"isbn": isbn}).fetchone()

    if book is None:
        return render_template("index.html", error_message="This book isbn doesn't exist, 404.")
    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "OCzrG88Hujx2LRMl0UyX2w", "isbns": book["isbn"]})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")

    gr_review = res.json()

    gr_ratings = {}
    gr_ratings['title'] = book['title']
    gr_ratings['author'] = book['author']
    gr_ratings['year'] = book['pb_year']
    gr_ratings['isbn'] = gr_review['books'][0]["isbn"]
    gr_ratings['reviews_count'] = gr_review['books'][0]["reviews_count"]
    gr_ratings['average_score'] = gr_review['books'][0]["average_rating"]
    #gr_ratings['id'] = gr_review['books'][0]["id"]
    #gr_ratings['isbn13'] = gr_review['books'][0]["isbn13"]
    #gr_ratings['ratings_count'] = gr_review['books'][0]["ratings_count"]
    #gr_ratings['text_reviews_count'] = gr_review['books'][0]["text_reviews_count"]
    #gr_ratings['work_ratings_count'] = gr_review['books'][0]["work_ratings_count"]
    #gr_ratings['work_reviews_count'] = gr_review['books'][0]["work_reviews_count"]
    #gr_ratings['work_text_reviews_count'] = gr_review['books'][0]["work_text_reviews_count"]

    return gr_ratings


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
        return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    app.run(debug=True)