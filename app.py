import os
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import sqlite3
import subprocess
from static.database.init_db import init_db


BASE_DIR = os.path.dirname(__file__)  # Folder of app.py
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

comments_storage = []  # In-memory: list of {"id": int, "text": str}
comment_id_counter = 1

user_files = {}
file_id_counter = 1

app = Flask(__name__)
app.secret_key = "supersecret_insecure_key"


@app.route("/")
def index():
    # Simple home page
    if "username" in session:
        logged_in_html = f"<p>Logged in as {session['username']} | <a href='/logout' class='button'>Logout</a></p>"
    else:
        logged_in_html = "<p><a href='/login' class='button'>Login</a></p>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>BugBox</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h1>Welcome to BugBox!</h1>
            {logged_in_html}
            <p><a href="/user_home" class="button">Go to User Home</a></p>
            <p>This is the home page.</p>
            <form action="/reset_db" method="POST" style="display:inline;">
                <button type="submit" class="button danger">Reset Database</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Intentionally vulnerable SQL query
        conn = sqlite3.connect("static/database/bugbox.db")
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        c.execute(query)
        result = c.fetchone()
        conn.close()

        if result:
            session["username"] = username  # No role check => Broken Access Control
            return redirect(url_for("user_home"))
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login Failed</title>
                <link rel="stylesheet" type="text/css" href="/static/styles.css">
            </head>
            <body>
                <div class="container">
                    <h3>Login failed.</h3>
                    <p><a href='/login' class="button">Back to Login</a></p>
                </div>
            </body>
            </html>
            """
    else:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h1>Login</h1>
                <form method="POST" action="/login" class="form">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" placeholder="Enter Username" class="input" required>
                    <br><br>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" placeholder="Enter Password" class="input" required>
                    <br><br>
                    <button type="submit" class="button">Login</button>
                </form>
                <p><a href="/" class="button">Back to Home</a></p>
            </div>
        </body>
        </html>
        """

@app.route("/logout")
def logout():
    session.clear()
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logout</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h1>Logged Out</h1>
            <p>You have successfully logged out.</p>
            <p><a href="/" class="button">Return to Home</a></p>
        </div>
    </body>
    </html>
    """


@app.route("/admin")
def admin():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Panel</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to view the admin page.</p>
                <p><a href='/login' class="button">Go to Login</a></p>
            </div>
        </body>
        </html>
        """

    # BROKEN ACCESS CONTROL: Any logged-in user can access this page
    conn = sqlite3.connect("static/database/bugbox.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users")
    users = c.fetchall()
    conn.close()

    if len(users) == 0:
        table_html = "<p>No users found in the database.</p>"
    else:
        table_html = """
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Password</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """
        for user_id, uname, pw in users:
            table_html += f"""
                <tr>
                    <td>{user_id}</td>
                    <td>{uname}</td>
                    <td>{pw}</td>
                    <td>
                        <form action="/delete_user" method="POST">
                            <input type="hidden" name="user_id" value="{user_id}">
                            <button type="submit" class="button danger">Delete</button>
                        </form>
                    </td>
                </tr>
            """
        table_html += """
            </tbody>
        </table>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h1>Admin Panel</h1>
            <p>Welcome, Admin!)</p>
            {table_html}
            <p><a href="/" class="button">Go to Home</a> | <a href="/logout" class="button">Logout</a></p>
        </div>
    </body>
    </html>
    """


@app.route("/delete_user", methods=["POST"])
def delete_user():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Access Denied</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to delete users.</p>
                <p><a href='/login' class="button">Go to Login</a></p>
            </div>
        </body>
        </html>
        """

    user_id = request.form.get("user_id")
    if not user_id:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No user ID provided for deletion.</p>
                <p><a href='/admin' class="button">Back to Admin</a></p>
            </div>
        </body>
        </html>
        """

    conn = sqlite3.connect("static/database/bugbox.db")
    c = conn.cursor()
    try:
        c.execute(f"DELETE FROM users WHERE id = {user_id}")  # Insecure: SQL Injection Vulnerability
        conn.commit()
        message = f"User {user_id} has been deleted successfully."
    except Exception as e:
        message = f"Failed to delete user {user_id}: {str(e)}"
    finally:
        conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delete User</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h3>Delete User</h3>
            <p>{message}</p>
            <p><a href='/admin' class="button">Back to Admin</a></p>
        </div>
    </body>
    </html>
    """



@app.route("/user_home", methods=["GET", "POST"])
def user_home():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>User Home</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to view your user home.</p>
                <p><a href='/login' class="button">Go to Login</a></p>
            </div>
        </body>
        </html>
        """

    global comment_id_counter, file_id_counter
    username = session["username"]
    feedback_message = ""

    if username not in user_files:
        user_files[username] = []

    if request.method == "POST":
        form_type = request.form.get("form_type", "")
        if form_type == "comment":
            user_input = request.form.get("comment")
            comments_storage.append({
                "id": comment_id_counter,
                "text": user_input
            })
            comment_id_counter += 1
            feedback_message = "<p class='success'>Comment posted successfully!</p>"

        elif form_type == "upload":
            file_obj = request.files.get("uploaded_file")
            if file_obj and file_obj.filename:
                filename = file_obj.filename
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file_obj.save(save_path)

                user_files[username].append({
                    "file_id": file_id_counter,
                    "filename": filename
                })
                file_id_counter += 1

                feedback_message = f"<p class='success'>File '{filename}' uploaded successfully!</p>"
            else:
                feedback_message = "<p class='error'>No file selected or empty filename!</p>"

    # Build Comments
    comments_html = ""
    for comment in comments_storage:
        c_id = comment["id"]
        c_text = comment["text"]
        comments_html += f"""
        <div class="comment">
            <p><strong>Comment {c_id}:</strong> {c_text}</p>
            <form action="/delete_comment" method="POST" style="display:inline;">
                <input type="hidden" name="comment_id" value="{c_id}">
                <button type="submit" class="button danger">Delete</button>
            </form>
        </div>
        """

    # Build File List
    files_html = ""
    for f_info in user_files[username]:
        fid = f_info["file_id"]
        fname = f_info["filename"]
        files_html += f"""
        <div class="file">
            <p><strong>File:</strong> {fname}</p>
            <form action="/view_or_run" method="POST" style="display:inline;">
                <input type="hidden" name="file_id" value="{fid}">
                <button type="submit" class="button">View</button>
            </form>
            <form action="/delete_file" method="POST" style="display:inline;">
                <input type="hidden" name="file_id" value="{fid}">
                <button type="submit" class="button danger">Delete</button>
            </form>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>User Home</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h2>Welcome, {username}!</h2>
            <p>This is your personal blog page. "View/Run File" will open files or run .exe/.bat!</p>
            {feedback_message}

            <!-- Comment Form -->
            <h3>Post a Comment</h3>
            <form method="POST" action="/user_home">
                <input type="hidden" name="form_type" value="comment"/>
                <textarea name="comment" rows="3" cols="50" class="input"></textarea><br><br>
                <button type="submit" class="button">Post Comment</button>
            </form>

            <h3>Your Comments</h3>
            <div class="comments-section">
                {comments_html}
            </div>

            <!-- File Upload Form -->
            <h3>Upload a File</h3>
            <form method="POST" action="/user_home" enctype="multipart/form-data">
                <input type="hidden" name="form_type" value="upload"/>
                <input type="file" name="uploaded_file" class="input"/>
                <button type="submit" class="button">Upload</button>
            </form>

            <h3>Your Files</h3>
            <div class="files-section">
                {files_html}
            </div>

            <p><a href="/" class="button">Go Home</a> | <a href="/logout" class="button">Logout</a></p>
        </div>
    </body>
    </html>
    """




@app.route("/delete_comment", methods=["POST"])
def delete_comment():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete Comment</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to delete comments.</p>
                <p><a href='/login' class="button">Go to Login</a></p>
            </div>
        </body>
        </html>
        """

    comment_id = request.form.get("comment_id")
    if not comment_id:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete Comment</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No comment ID provided.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    try:
        cid = int(comment_id)
    except ValueError:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete Comment</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>Invalid comment ID: '{comment_id}'</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    # Find and delete the comment
    global comments_storage
    for i, comment in enumerate(comments_storage):
        if comment["id"] == cid:
            del comments_storage[i]
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Delete Comment</title>
                <link rel="stylesheet" type="text/css" href="/static/styles.css">
            </head>
            <body>
                <div class="container">
                    <h3>Success</h3>
                    <p>Comment {cid} deleted successfully!</p>
                    <p><a href='/user_home' class="button">Back to User Home</a></p>
                </div>
            </body>
            </html>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delete Comment</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h3>Error</h3>
            <p>Comment {cid} not found.</p>
            <p><a href='/user_home' class="button">Back to User Home</a></p>
        </div>
    </body>
    </html>
    """




@app.route("/view_or_run", methods=["POST"])
def view_or_run():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>View or Run File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to view or run files.</p>
                <p><a href='/login' class="button">Login</a></p>
            </div>
        </body>
        </html>
        """

    file_id = request.form.get("file_id")
    if not file_id:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>View or Run File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No file ID provided.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    username = session["username"]
    if username not in user_files:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>View or Run File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No files found for user '{username}'.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    try:
        fid = int(file_id)
    except ValueError:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>View or Run File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>Invalid file ID '{file_id}'.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    for file_info in user_files[username]:
        if file_info["file_id"] == fid:
            filename = file_info["filename"]
            file_path = os.path.join(UPLOAD_FOLDER, filename)

            if not os.path.exists(file_path):
                return f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>View or Run File</title>
                    <link rel="stylesheet" type="text/css" href="/static/styles.css">
                </head>
                <body>
                    <div class="container">
                        <h3>Error</h3>
                        <p>File '{filename}' not found on disk.</p>
                        <p><a href='/user_home' class="button">Back to User Home</a></p>
                    </div>
                </body>
                </html>
                """

            _, extension = os.path.splitext(filename)
            extension = extension.lower()

            if extension in [".exe", ".bat"]:
                try:
                    subprocess.Popen(file_path, shell=True)
                    return f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Run File</title>
                        <link rel="stylesheet" type="text/css" href="/static/styles.css">
                    </head>
                    <body>
                        <div class="container">
                            <h3>Success</h3>
                            
                            <p><a href='/user_home' class="button">Back to User Home</a></p>
                        </div>
                    </body>
                    </html>
                    """
                except Exception as e:
                    return f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Run File</title>
                        <link rel="stylesheet" type="text/css" href="/static/styles.css">
                    </head>
                    <body>
                        <div class="container">
                            <h3>Error</h3>
                            <p>Failed to run '{filename}': {e}</p>
                            <p><a href='/user_home' class="button">Back to User Home</a></p>
                        </div>
                    </body>
                    </html>
                    """

            return send_from_directory(UPLOAD_FOLDER, filename)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>View or Run File</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h3>Error</h3>
            <p>File with ID {file_id} not found.</p>
            <p><a href='/user_home' class="button">Back to User Home</a></p>
        </div>
    </body>
    </html>
    """



@app.route("/delete_file", methods=["POST"])
def delete_file():
    if "username" not in session:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Access Denied</h3>
                <p>You must be logged in to delete files.</p>
                <p><a href='/login' class="button">Login</a></p>
            </div>
        </body>
        </html>
        """

    file_id = request.form.get("file_id")
    if not file_id:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No file ID provided.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    username = session["username"]
    if username not in user_files:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>No files found for user '{username}'.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    try:
        fid = int(file_id)
    except ValueError:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete File</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>Error</h3>
                <p>Invalid file ID '{file_id}'.</p>
                <p><a href='/user_home' class="button">Back to User Home</a></p>
            </div>
        </body>
        </html>
        """

    for i, finfo in enumerate(user_files[username]):
        if finfo["file_id"] == fid:
            filename = finfo["filename"]
            del user_files[username][i]

            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(file_path):
                os.remove(file_path)

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Delete File</title>
                <link rel="stylesheet" type="text/css" href="/static/styles.css">
            </head>
            <body>
                <div class="container">
                    <h3>Success</h3>
                    <p>File '{filename}' deleted successfully.</p>
                    <p><a href='/user_home' class="button">Back to User Home</a></p>
                </div>
            </body>
            </html>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delete File</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h3>Error</h3>
            <p>File with ID {file_id} not found.</p>
            <p><a href='/user_home' class="button">Back to User Home</a></p>
        </div>
    </body>
    </html>
    """

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    """
    Serve the uploaded files from the static/uploads folder.
    Potentially dangerous if your server can execute files like .php, .asp, etc.
    """
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/reset_db", methods=["POST"])
def reset_db():
    if "username" not in session:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reset Database</title>
            <link rel="stylesheet" type="text/css" href="/static/styles.css">
        </head>
        <body>
            <div class="container">
                <h3>You must be logged in!</h3>
                <p><a href='/login' class="button">Go to Login</a></p>
            </div>
        </body>
        </html>
        """


    init_db()

    # Reset in-memory data
    comments_storage.clear()
    global comment_id_counter
    comment_id_counter = 1

    # Also clear user_files dictionary and file_id_counter
    user_files.clear()
    global file_id_counter
    file_id_counter = 1

    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Reset</title>
        <link rel="stylesheet" type="text/css" href="/static/styles.css">
    </head>
    <body>
        <div class="container">
            <h3>Database has been reset!</h3>
            <p>All tables dropped and re-initialized. 
            In-memory data cleared (comments & file references).</p>
            <p><a href='/' class="button">Back to Home</a></p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
