from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from functools import wraps
import os

app = Flask(__name__)

# ==========================================
# AZURE CONFIG
# ==========================================

app.secret_key = "liga-secret-123"

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "liga.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ==========================================
# USERS
# ==========================================

USERS = {
    "admin": {"password": "admin", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# ==========================================
# MODELS
# ==========================================

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer)
    away_team_id = db.Column(db.Integer)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer)
    goals = db.Column(db.Integer)

# ==========================================
# INIT DB
# ==========================================

with app.app_context():
    db.create_all()

    if Team.query.count() == 0:
        t1 = Team(name="Legia")
        t2 = Team(name="Lech")
        t3 = Team(name="Wisła")

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        db.session.add_all([
            Player(name="Kowalski", team_id=t1.id),
            Player(name="Nowak", team_id=t2.id),
            Player(name="Zieliński", team_id=t3.id),
        ])
        db.session.commit()

# ==========================================
# DECORATOR
# ==========================================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return "Brak uprawnień", 403
        return f(*args, **kwargs)
    return wrapper

# ==========================================
# LOGIC
# ==========================================

def table():
    teams = Team.query.all()
    result = []

    for t in teams:
        pts = 0

        home = Game.query.filter_by(home_team_id=t.id).all()
        away = Game.query.filter_by(away_team_id=t.id).all()

        for g in home:
            if g.home_score > g.away_score:
                pts += 3
            elif g.home_score == g.away_score:
                pts += 1

        for g in away:
            if g.away_score > g.home_score:
                pts += 3
            elif g.away_score == g.home_score:
                pts += 1

        result.append({"team": t.name, "points": pts})

    return sorted(result, key=lambda x: x["points"], reverse=True)

def top_scorer():
    res = db.session.query(
        Player.name,
        func.sum(Goal.goals).label("g")
    ).join(Goal, Goal.player_id == Player.id)\
     .group_by(Player.id)\
     .order_by(func.sum(Goal.goals).desc())\
     .first()

    if not res:
        return type("P", (), {"name": "-", "g": 0})

    return res

# ==========================================
# LOGIN
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u in USERS and USERS[u]["password"] == p:
            session["user"] = u
            session["role"] = USERS[u]["role"]
            return redirect("/")

        error = "Błędny login"

    return f"""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <div class="container mt-5" style="max-width:400px;">
        <div class="card p-4 shadow">
            <h3>⚽ Login</h3>

            <form method="POST">
                <input class="form-control mb-2" name="username" placeholder="login">
                <input class="form-control mb-2" type="password" name="password" placeholder="hasło">
                <button class="btn btn-primary w-100">Zaloguj</button>
            </form>

            <p class="text-danger">{error}</p>

            <small>admin/admin | user/user</small>
        </div>
    </div>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==========================================
# ADD DATA (ADMIN)
# ==========================================

@app.route("/add_team", methods=["GET", "POST"])
@admin_required
def add_team():
    if request.method == "POST":
        db.session.add(Team(name=request.form["name"]))
        db.session.commit()
        return redirect("/")
    return "<form method='POST'><input name='name'><button>OK</button></form>"

@app.route("/add_game", methods=["GET", "POST"])
@admin_required
def add_game():
    teams = Team.query.all()

    if request.method == "POST":
        db.session.add(Game(
            home_team_id=request.form["home"],
            away_team_id=request.form["away"],
            home_score=request.form["hs"],
            away_score=request.form["as"]
        ))
        db.session.commit()
        return redirect("/")

    form = "<form method='POST'>"
    form += "<select name='home'>"
    for t in teams:
        form += f"<option value='{t.id}'>{t.name}</option>"
    form += "</select>"

    form += "<select name='away'>"
    for t in teams:
        form += f"<option value='{t.id}'>{t.name}</option>"
    form += "</select>"

    form += "<input name='hs' placeholder='home'><input name='as' placeholder='away'>"
    form += "<button>OK</button></form>"

    return form

@app.route("/add_player", methods=["GET", "POST"])
@admin_required
def add_player():
    teams = Team.query.all()

    if request.method == "POST":
        db.session.add(Player(
            name=request.form["name"],
            team_id=request.form["team"]
        ))
        db.session.commit()
        return redirect("/")

    form = "<form method='POST'>"
    form += "<input name='name'>"
    form += "<select name='team'>"

    for t in teams:
        form += f"<option value='{t.id}'>{t.name}</option>"

    form += "</select><button>OK</button></form>"
    return form

# ==========================================
# HOME UI
# ==========================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Liga PRO</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body { background:#eef2f7; }
.card { border-radius:15px; }
</style>
</head>

<body>

<div class="container mt-4">

<div class="d-flex justify-content-between">
<h2>⚽ Liga PRO</h2>

<div>
<b>{{ user }}</b>
<a href="/login" class="btn btn-sm btn-primary">Login</a>
<a href="/logout" class="btn btn-sm btn-danger">Logout</a>
</div>
</div>

{% if role == "admin" %}
<div class="mb-3">
<a href="/add_team" class="btn btn-primary">Drużyna</a>
<a href="/add_game" class="btn btn-warning">Mecz</a>
<a href="/add_player" class="btn btn-success">Zawodnik</a>
</div>
{% endif %}

<div class="card p-3 mb-3">
<h4>🏆 Tabela</h4>

<table class="table">
<tr><th>#</th><th>Drużyna</th><th>Punkty</th></tr>

{% for t in table %}
<tr>
<td>{{ loop.index }}</td>
<td>{{ t.team }}</td>
<td>{{ t.points }}</td>
</tr>
{% endfor %}

</table>
</div>

<div class="card p-3 mb-3">
<h4>⭐ Król strzelców</h4>
<b>{{ scorer.name }}</b> - {{ scorer.g }} goli
</div>

</div>

</body>
</html>
"""

# ==========================================
# ROUTE
# ==========================================

@app.route("/")
def home():
    return render_template_string(
        HTML,
        user=session.get("user", "guest"),
        role=session.get("role", "guest"),
        table=table(),
        scorer=top_scorer()
    )

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run()
