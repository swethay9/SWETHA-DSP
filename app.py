from flask import Flask, render_template, request, redirect, session, jsonify
import hashlib
import pymysql

app = Flask(__name__)
app.secret_key = "secure_key"  # For session management

# Database connection
db = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="secure_db"
)

# Hashing function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Route: Index
@app.route("/")
def index():
    return render_template("index.html")

# Route: Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        cursor = db.cursor()
        cursor.execute("SELECT username, group_name FROM users WHERE username=%s AND password_hash=%s", (username, password))
        user = cursor.fetchone()
        
        if user:
            session["username"] = user[0]
            session["group"] = user[1]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid username or password!")
    return render_template("login.html")

# Route: Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        group = request.form["group"]

        cursor = db.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash, group_name) VALUES (%s, %s, %s)", (username, password, group))
            db.commit()
            return redirect("/login")
        except:
            return render_template("register.html", error="Username already exists!")
    return render_template("register.html")

# Route: Dashboard
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    group = session["group"]
    return render_template("dashboard.html", group=group)

# Route: Query Data
@app.route("/query", methods=["GET"])
def query_data():
    if "username" not in session:
        return redirect("/login")
    
    group = session["group"]
    query = "SELECT * FROM healthcare"
    
    if group == "R":
        query = "SELECT gender, age, weight, height, health_history FROM healthcare"

    cursor = db.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    return render_template("query.html", data=data, group=group)

# Route: Edit Data (Group H Only)
@app.route("/edit/<int:id>", methods=["POST"])
def edit_data(id):
    if "username" not in session or session["group"] != "H":
        return redirect("/login")

    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    gender = request.form["gender"]
    age = request.form["age"]
    weight = request.form["weight"]
    height = request.form["height"]
    health_history = request.form["health_history"]

    cursor = db.cursor()
    cursor.execute("""
        UPDATE healthcare
        SET first_name=%s, last_name=%s, gender=%s, age=%s, weight=%s, height=%s, health_history=%s
        WHERE id=%s
    """, (first_name, last_name, gender, age, weight, height, health_history, id))
    db.commit()
    
    return redirect("/query")

# Route: Add Data (Group H Only)
@app.route("/add", methods=["GET", "POST"])
def add_data():
    if "username" not in session or session["group"] != "H":
        return redirect("/login")
    
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        gender = request.form["gender"]
        age = request.form["age"]
        weight = request.form["weight"]
        height = request.form["height"]
        health_history = request.form["health_history"]

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO healthcare (first_name, last_name, gender, age, weight, height, health_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, gender, age, weight, height, health_history))
        db.commit()
        return redirect("/dashboard")
    return render_template("add_data.html")

# Route: Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
