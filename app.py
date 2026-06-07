from flask import Flask, render_template_string, request, redirect, session

app = Flask(__name__)

# ==========================================
# AZURE SESSION FIX
# ==========================================

app.secret_key = "super-secret-key-123"

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

# ==========================================
# USERS
# ==========================================

USERS = {
    "admin": "admin",
    "user": "user"
}

# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username] == password:
            session["user"] = username
            session["role"] = username
            return redirect("/")

        error = "Błędny login lub hasło"

    return f"""
    <h2>Login</h2>

    <form method="POST">
        <input name="username" placeholder="login"><br><br>
        <input type="password" name="password" placeholder="hasło"><br><br>
        <button>Login</button>
    </form>

    <p style='color:red'>{error}</p>

    <p>admin/admin | user/user</p>
    """

# ==========================================
# LOGOUT (FIXED)
# ==========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==========================================
# HOME
# ==========================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Liga</title>
</head>
<body style="font-family: Arial; background:#f5f5f5;">

<div style="padding:20px; background:white; margin:20px; border-radius:10px;">

<h2>⚽ Liga1</h2>

<p>
Zalogowany: <b>{{ user }}</b>
</p>

<a href="/logout">Wyloguj</a> |
<a href="/login">Login</a>

<hr>

{% if user == "admin" %}

<h3>Panel admina</h3>
<button>Dodaj drużynę</button>
<button>Dodaj mecz</button>

{% elif user == "user" %}

<h3>Widok usera</h3>
<p>Możesz tylko przeglądać dane</p>

{% else %}

<h3>Gość</h3>
<p>Zaloguj się aby zobaczyć więcej</p>

{% endif %}

</div>

</body>
</html>
"""

@app.route("/")
def home():
    user = session.get("user", "guest")

    return render_template_string(
        HTML,
        user=user
    )

# ==========================================
# START (AZURE SAFE)
# ==========================================

if __name__ == "__main__":
    app.run()
