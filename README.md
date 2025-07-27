# Ivan Bebić - CV
#### Video Demo:
#### Description:

My idea for this project was to create an application that serves as my personal resume. 
The purpose of this application is to help me in future job applications.
Application is build using Python with the Flask framework and Jinja templating.
I also used some Flask extensions for email sending (flask_mail), session menagment(flask_session) and for hiding sensitive informations, I used dotenv.
Looks of the application is created in HTML and CSS.

For the project, I created a base.html template that contains the header and footer of the application, since these elements are the same on every page. 
The header includes links to all pages of the application, while the footer contains my contact information such as phone number, email, LinkedIn, and GitHub.

The home page is written in index.html using Jinja and HTML. 
The GET method for this route is defined in app.py. 
On the homepage, there is a welcome message for the user and my resume content. 
I wrote about my work experience, education, skills, hobbies, and more.
The page is divided into a guest and admin section. 
Guests can access the content without logging in, while admins get additional functionality after logging in. 
Login informations and email-related settings (explained later) are stored in the .env file.

The next page is projects.html. 
This page is rendered with a GET method in app.py, and it receives data from the database about available programming languages and project types. 
This allows users to filter the kinds of projects they want to view.
After selecting filters, a POST request is made and matching projects are retrieved from the database and displayed. 
Each project in the database contains a name, description, image, programming language, project type, and a link to the project.

If an admin is logged in, they can delete a project from the database.
Admins also have access to add.html, which allows them to add a new project. 
By clicking "Add" in the top-right corner, they can fill in all the necessary information to store a project in the database. 
The image associated with the project is given a unique filename and stored in the static/img/ folder, and the entire project is then saved to the database.
For the image, only filename is stored.

The next page is contact.html. 
After the GET request for the /contact route, the user is shown a form where they can leave a message as an email. 
The user enters their message and email address, and then receives a six-digit verification code generated randomly. 
They are then redirected to /verify, which displays the verify.html page. 
Here, they enter the verification code. 
If the code is correct, the admin receives an email with the user's message and email address. 
I implemented the verification code to prevent users from impersonating others. 
If a user enters the wrong code three times, they lose the ability to send messages for the rest of the day. 
Additionally, users can send a maximum of five emails per day.
In app.py, I added server side protections to prevent malicious actions coming from the frontend, such as changing HTML code on the client side.

The application also allows users to download my resume. 
When they click the download option, the PDF version of my resume opens in a new tab and can be saved.

The application has only one admin, who can log in through the /login route. 
This route first renders the login form using login.html. 
In the POST method, the username and password are checked. 
The real username and password are available from .env file.
After two failed login attempts, login is disabled for that user for the rest of the day.

After logging in, the admin also has the option to log out with the /logout route. 
This is done using session.clear(), which removes all session data. 
Logging out, as well as adding and deleting projects, requires the user to be logged in. 
Project deletion happens with the /remove route, which is protected with @login_required (same as /add and /logout). 
The project is located by its ID and removed from the database.

The design of the application is handled in the style.css file, and it is responsive based on screen size. 
CSS is not complex, because I wanted minimalistic look.

The database is created using SQLite and is named cv.db. 
It contains three tables:

languages – stores programming languages with their IDs and names which users can use as filters.

project_type – stores different types of projects like web development, game development, OOP, etc., which users can also use as filters.

projects – contains the project ID, name, description, image filename, project link, and foreign keys linking to the language and project type.

The .env file contains information such as the mail server and port for sending emails. 
It also includes sensitive data like my email credentials, used for sending the verification code and messages. 
Additionally, it stores admin login credentials. 
I added the .env file to .gitignore to ensure it does not get published to GitHub when I push the project.

