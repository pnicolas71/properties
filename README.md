# Project 1 - Books

Registration: Users should be able to register for your website, providing (at minimum) a username and password.
    - register.html (request First Name, Last Name, email, password and confirmation password 
    - Returns error if any value is missing or if email already registered.
    - The username is the email address
Login: Users, once registered, should be able to log in to your website with their username and password.
    - Requests login email and password
    - returns error if email and/or password is misssing or wrong.
Logout: Logged in users should be able to log out of the site.
    - after login a success message is shown and user can search for books
Import: Provided for you in this project is a file called books.csv, 
    - the import of 5000 books was done by the python app import.py provided
Search: Once a user has logged in, they should be taken to a page where they can search for a book. Users should be able to type in the ISBN number of a book, the title of a book, or the author of a book. After performing the search, your website should display a list of possible matching results, or some sort of message if there were no matches. If the user typed in only part of a title, ISBN, or author name, your search page should find matches for those as well!
    - Process done, doesn't take the case in account and searches all data part ot complete of isbn, author, title
Book Page: 
    -show book page with all the information requested: ISBN, Title, Author, Book Year
    - Good Reads average Rating and ratings count.
Review Submission: On the book page, users should be able to submit a review: consisting of a rating on a scale of 1 to 5, as well as a text component to the review where the user can write their opinion about a book. Users should not be able to submit multiple reviews for the same book.
    - Option to post a review from the book page: add a rating from 1 to 5 and add a text review
    - Can't add a review if the user already added a review
Goodreads Review Data: On your book page, you should also display (if available) the average rating and number of ratings the work has received from Goodreads.
    - Automatically shown in reviews
API Access: If users make a GET request to your website’s /api/<isbn> route, where <isbn> is an ISBN number, your website should return a JSON response containing the book’s title, author, publication date, ISBN number, review count, and average score. The resulting JSON should follow the format:
    -Shown as requested by entering the link API/<isbn>
