from flask import Flask, request, jsonify, render_template, redirect, session
import sqlite3, re

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("users.db")

def parse_command(text):
    text = text.lower().strip()

    # ADD
    add = re.search(r'add.*?([\w\.-]+@[\w\.-]+).*?(?:phone|number)?\s*([+\d]+)?', text)
    if add:
        email = add.group(1)
        phone = add.group(2) if add.group(2) else ""
        return ("add", email, phone)

    # REMOVE
    remove = re.search(r'(remove|delete).*?([\w\.-]+@[\w\.-]+)', text)
    if remove:
        return ("remove", remove.group(2))

    # UPDATE CITY
    update = re.search(r'update.*?([\w\.-]+).*?city.*?to\s+(\w+)', text)
    if update:
        return ("update", update.group(1), update.group(2))

    return ("unknown",)

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]

    db = get_db()
    cur = db.cursor()

    # Check admin
    cur.execute("SELECT * FROM admins WHERE email=?", (email,))
    admin = cur.fetchone()

    if admin:
        session.clear()
        session["admin"] = email
        return jsonify(role="admin")

    # Check user
    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    if user:
        session.clear()
        session["user"] = email
        return jsonify(role="user")

    return jsonify(role="fail")

@app.route("/chatpage")
def chatpage():
    if "admin" not in session:
        return redirect("/")
    return render_template("chat.html")

@app.route("/userpage")
def userpage():
    if "user" not in session:
        return redirect("/")
    return render_template("user.html")

@app.route("/chat", methods=["POST"])
def chat():
    if "admin" not in session:
        return jsonify(reply="Only admin can use chatbot")

    msg = request.json["message"]
    intent = parse_command(msg)

    db = get_db()
    cur = db.cursor()

    if intent[0] == "add":
        email, phone = intent[1], intent[2]
        try:
            cur.execute("INSERT INTO users(email, phone) VALUES (?,?)",(email,phone))
            db.commit()
            return jsonify(reply="User added")
        except:
            return jsonify(reply="User already exists")

    elif intent[0] == "remove":
        email = intent[1]
        cur.execute("DELETE FROM users WHERE email=?",(email,))
        db.commit()
        return jsonify(reply="User removed")

    elif intent[0] == "update":
        name, city = intent[1], intent[2]
        cur.execute("UPDATE users SET city=? WHERE email LIKE ?",(city,f"%{name}%"))
        db.commit()
        return jsonify(reply="User updated")

    else:
        return jsonify(reply="I did not understand")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(debug=True)
