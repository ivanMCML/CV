import os
import random
import sqlite3

from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask, flash, g, redirect, render_template, request, send_file, session
from flask_mail import Mail, Message
from flask_session import Session
from functools import wraps
from itertools import count
from werkzeug.utils import secure_filename

# Load .env file
load_dotenv()  # ChatGPT told me to use this line

# Configure application
app = Flask(__name__)

# Session lasts one day
app.permanent_session_lifetime = timedelta(days=1)

# Enable flash messages
app.secret_key = os.getenv("SECRET_KEY")  # ChatGPT told me to use this line

# Configure session to use filesystem instead of signed cookies
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite usage
app.config["DATABASE"] = "instance/cv.db"

# Configure for sending mails
app.config.update(
   MAIL_SERVER=os.getenv("MAIL_SERVER"),
   MAIL_PORT=int(os.getenv("MAIL_PORT")),
   MAIL_USE_TLS=os.getenv("MAIL_USE_TLS") == "True",
   MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
   MAIL_PASSWORD=os.getenv("MAIL_PASSWORD")
)

mail = Mail(app)  # ChatGPT told me to use this line


# Make session permanent
@app.before_request
def session_permanent():
   session.permanent = True

# ChatGPT helped with this function
# Open database
def get_db():
   if "db" not in g:
      g.db = sqlite3.connect(app.config["DATABASE"])
      g.db.row_factory = sqlite3.Row 
   return g.db

# ChatGPT helped with this function
# Close database
@app.teardown_appcontext
def close_db(error):
   db = g.pop("db", None)
   if db is not None:
      db.close()


# Ensure the admin is logged in
def admin_required(f):   
   @wraps(f)

   def decorated_function(*args, **kwargs):
      if not session.get('admin'):
         return redirect("/")
      return f(*args, **kwargs)
  
   return decorated_function


# Add new projects to the db
@app.route("/add", methods = ["GET", "POST"])
@admin_required
def add():

   db = get_db()
   
   # If method is get, show add.html
   if request.method == "GET":
      
      # Get all programing languages and project types from database
      rows = db.execute("SELECT * FROM language").fetchall()   # ChatGPT told me about fetchall() function
      languages = (dict(row) for row in rows)

      rows = db.execute("SELECT * FROM project_type").fetchall()
      project_type = (dict(row) for row in rows)

      return render_template("add.html", admin = session.get('admin', False), languages = languages, types = project_type)

   # If method is post
   else:
     
      # Check if admin entered project name
      name = request.form.get("name")
      if not name:
         flash("Name required")
         return redirect("/add")
    
      # Check if admin entered project description
      description = request.form.get("description")
      if not description:
         flash("Description required")
         return redirect("/add")
    
      # Check if admin entered project link
      link = request.form.get("link")
      if not link:
         flash("Link required")
         return redirect("/add")
    
      # Check if admin uploaded image
      image = request.files["image"]
      if not image or image.filename == "":
         flash("Image required")
         return redirect("/add")
    
      # Check if admin picked programming language
      language = request.form.get("language")
      if not language:
         flash("Programming language required")
         return redirect("/add")
    
      # Check if admin picked project type
      project_type = request.form.get("project_type")
      if not project_type:
         flash("Project type required")
         return redirect("/add")
    
      # Format image filename
      filename = secure_filename(image.filename)
      temp_filename = filename

      for i in count(0):
         if i:
            # If filename already exists, create new one
            temp_filename = f"{i}_{filename}"
       
         # Look for duplicate
         rows = db.execute("SELECT * FROM projects WHERE image = ?", (temp_filename,)).fetchall()
         
         # If there are no duplicates, confirm file name
         if not rows:
            filename = temp_filename
            break

      # Save image in static/image/ 
      image.save(os.path.join("static", "img", filename))
      
      # Insert project into database
      db.execute(
         "INSERT INTO projects(name, image, description, link, language_id, type_id)"
         "VALUES (?, ?, ?, ?, ?, ?)",
         (name, filename, description, link, language, project_type))
      db.commit()
    
      # Return admin back to the /add
      flash("Projekt uspješno dodan")
      return redirect("/add")


# Contact form
@app.route("/contact", methods = ["GET", "POST"])
def contact():
  
   # If method is get, show contact form
   if request.method == "GET":
      return render_template("contact.html", admin = session.get('admin', False))
      
   # If method is post
   elif request.method == "POST":

      # Block access after three failed verification attempts
      if session.get("verification_failed", 0) >= 3:
         flash("Access denied due to too many failed verification attempts.")
         return redirect("/forbidden")
      
      # If user sent five mails today, block acces
      if session.get("mails_sent", 0) >= 5:
         flash("You've reached the maximum number of email requests for today. Please try again tomorrow.")
         return redirect("/forbidden")
                         
      # Check if user entered an email
      email = request.form.get("email")
      if not email:
         flash("Email required!")
         return redirect("/contact")
      
      # Check if user wrote a message
      content = request.form.get("content")
      if not content:
         flash("Message box is empty!")
         return redirect("/contact")

      # Generate six-digit verification code
      verification_code = f"{random.randint(0, 999999):06d}"  

      # Store data into session
      session['verification_code'] = verification_code
      session['email'] = email
      session['content'] = content

      # ChatGPT helped with mail creating syntax
      # Create and send email with verification code
      msg = Message("Verify your email address",
                     sender = app.config["MAIL_USERNAME"],
                     recipients = [email])

      msg.body = f"Someone requested to use your email address. If this wasn't you, please ignore this message. If it was you, your verification code is:\n {verification_code}"
      
      mail.send(msg)

      # Redirect user to verification page
      return redirect("/verify")
   

# Show CV with download option
@app.route("/download-cv")
def download_cv():

   # Make a path
   path = os.path.join("static", "IvanBebic.pdf")
   return send_file(path)   # ChatGPT told me about this function


# Show error page
@app.route("/forbidden")
def forbidden():
   
   return render_template("forbidden.html", admin = session.get('admin', False))


# Open main page
@app.route("/")
def index():

   return render_template("index.html", admin = session.get('admin', False))


# Admin login
@app.route("/login", methods = ["GET", "POST"])
def login():

   # Block access after two failed login attempts
   if session.get("login_failed", 0) >= 2:
      flash("Access denied due to too many failed login attempts.")
      return redirect("/forbidden")

   # If method is get, show login form
   if request.method == "GET":
      return render_template("login.html", admin = session.get('admin', False)) 
  
   # If method is post
   elif request.method == "POST":
     
      # Check if user entered username
      username = request.form.get("email")
      if not username:
         flash("Username required!")
         return redirect("/login")
          
      # Check if user entered password
      password = request.form.get("password")
      if not password:
         flash("Enter the password!")
         return redirect("/login")
     
      # Check if username and password are correct
      if username == os.getenv("ADMIN_USERNAME") and password == os.getenv("ADMIN_PASSWORD"):
         # Create a session and redirect admin to the homepage
         session['admin'] = True
         return redirect("/")
     
      # If user failed to log in
      else:
         if "login_failed" not in session:
            session['login_failed'] = 0
         session['login_failed'] += 1

         flash("Wrong username or password!")
         return redirect("/login")


# Admin logout
@app.route("/logout")
@admin_required
def logout():
   
   # Forget any data from session, including admin = true
   session.clear()

   # Redirect user to homepage
   return redirect("/")


# Open projects page
@app.route("/projects", methods = ["GET", "POST"])
def projects():

   # Create db object
   db = get_db()
   
   # Get all programing languages and project types from database
   rows = db.execute("SELECT * FROM language").fetchall()
   all_languages = [dict(row) for row in rows]

   rows = db.execute("SELECT * FROM project_type").fetchall()
   all_project_types = [dict(row) for row in rows]
      

   # If method is get, show projects.html
   if request.method == "GET":
      
      # Get all projects from database
      rows = db.execute("SELECT * FROM projects").fetchall()
      all_projects = [dict(row) for row in rows]

      return render_template("projects.html", admin = session.get('admin', False), languages = all_languages, types = all_project_types, projects = all_projects)

  
   # Get all projects from database
   if request.method == "POST":

      # Get checked programming languages
      selected_languages = request.form.getlist("language")
      
      # Check if there are no prioritized programming languages
      if "all" in selected_languages or not selected_languages:
         rows = db.execute("SELECT * FROM projects").fetchall()

      # Get projects written in checked programming languages
      else:
         placeholders = ','.join(['?'] * len(selected_languages))
         query = f"SELECT * FROM projects WHERE language_id IN ({placeholders})"
         rows = db.execute(query, selected_languages).fetchall()

      projects_filtered_by_language = [dict(row) for row in rows]

      # Get checked project types
      selected_project_types = request.form.getlist("project_type")

      # If there are no prioritized types, return all projects
      if "all" in selected_project_types or not selected_project_types:
         selected_projects = projects_filtered_by_language

      # Get projects of certain type
      else:
         selected_projects = []
         for project in projects_filtered_by_language:
            if str(project["type_id"]) in selected_project_types:
               selected_projects.append(project)

      # Show projects
      return render_template("projects.html", admin = session.get('admin', False), languages = all_languages, types = all_project_types, projects = selected_projects)


# Remove project from database
@app.route("/remove", methods = ["GET", "POST"])
@admin_required
def remove():

   # If method is get, redirect admin to projects
   if request.method == "GET":
      return redirect("/projects")

   # If method is post
   else:

      # Get ids of projects to remove
      projects_to_remove = request.form.getlist("remove")

      # If there are no projects to remove, redirect admin to the projects
      if not projects_to_remove:
         return redirect("/projects")
      
      # Delete projects with matching ids
      placeholders = ','.join(['?'] * len(projects_to_remove))   # ChatGPT helped with this line
      query = f"DELETE FROM projects WHERE id IN ({placeholders})"
      db = get_db()
      db.execute(query, projects_to_remove)
      db.commit() # ChatGPT told me to use this function

      # Inform admin about success of action, and redirect him to homepage
      flash(f"Obrisano {len(projects_to_remove)} projekata.")
      return redirect("/")


# Verification
@app.route("/verify", methods = ["GET", "POST"])
def verify():
     
   # If method is get, show verification page
   if request.method == "GET":
      return render_template("verify.html", admin = session.get('admin', False))

   # If method is post
   else:
   
      # Check if user's session expired
      user_code = request.form.get("verify")
      if 'verification_code' not in session:
         flash("Session expired. Please try again.")
         return redirect("/contact")

      # Check if user entered correct verification code
      if user_code == session.get("verification_code"):
         
         # Create and send user's email to the admin
         msg = Message(f"Poruka od {session.get('email')} preko CV aplikacije",
                     sender = app.config["MAIL_USERNAME"],
                     recipients = [app.config["MAIL_USERNAME"]])
            
         msg.body = session['content']
         mail.send(msg)

         # Create a message to inform the user
         flash("Message sent")

         if "mails_sent" not in session:
            session['mails_sent'] = 0
         session['mails_sent'] += 1

         return redirect("/contact")

      # If user entered wrong verification code, inform the user  
      else:
         if "verification_failed" not in session:
            session['verification_failed'] = 0
         session['verification_failed'] += 1

         flash("Wrong verification code!")
         return redirect("/contact")
