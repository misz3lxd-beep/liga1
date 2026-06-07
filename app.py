from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from sqlalchemy import func
import os

app = Flask(__name__)

# ==========================================
# CONFIG
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
    team_id = db.Column(db.Integer)

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
# ADMIN DECORATOR
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
            elif g.away_score == g.away_score:
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

        error = "Błędne dane"

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
# ADMIN PANEL
# ==========================================

@app.route("/admin")
@admin_required
def admin():
    teams = Team.query.all()
    players = Player.query.all()

    return render_template_string("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <div class="container mt-5">

        <h2>🛠️ Panel Admina</h2>

        <div class="row mt-4">

            <!-- TEAM -->
            <div class="col-md-4">
                <div class="card p-3 shadow">
                    <h5>➕ Drużyna</h5>
                    <form method="POST" action="/add_team">
                        <input name="name" class="form-control mb-2">
                        <button class="btn btn-primary w-100">Dodaj</button>
                    </form>
                </div>
            </div>

            <!-- PLAYER -->
            <div class="col-md-4">
                <div class="card p-3 shadow">
                    <h5>👤 Zawodnik</h5>
                    <form method="POST" action="/add_player">
                        <input name="name" class="form-control mb-2">

                        <select name="team" class="form-select mb-2">
                            {% for t in teams %}
                                <option value="{{ t.id }}">{{ t.name }}</option>
                            {% endfor %}
                        </select>

                        <button class="btn btn-success w-100">Dodaj</button>
                    </form>
                </div>
            </div>

            <!-- GAME + GOALS -->
            <div class="col-md-4">
                <div class="card p-3 shadow">
                    <h5>⚽ Mecze</h5>
                    <a href="/add_game" class="btn btn-warning w-100">Dodaj mecz</a>

                    <a href="/add_goals" class="btn btn-dark w-100 mt-2">
                        🎯 Dodaj gole
                    </a>
                </div>
            </div>

        </div>

        <a href="/" class="btn btn-secondary mt-3">Powrót</a>

    </div>
    """, teams=teams)

# ==========================================
# ADD TEAM
# ==========================================

@app.route("/add_team", methods=["POST"])
@admin_required
def add_team():
    db.session.add(Team(name=request.form["name"]))
    db.session.commit()
    return redirect("/admin")

# ==========================================
# ADD PLAYER
# ==========================================

@app.route("/add_player", methods=["POST"])
@admin_required
def add_player():
    db.session.add(Player(
        name=request.form["name"],
        team_id=request.form["team"]
    ))
    db.session.commit()
    return redirect("/admin")

# ==========================================
# ADD GAME
# ==========================================

@app.route("/add_game", methods=["GET", "POST"])
@admin_required
def add_game():
    teams = Team.query.all()
    error = ""

    if request.method == "POST":
        home = request.form["home"]
        away = request.form["away"]

        if home == away:
            error = "❌ Nie można grać przeciwko sobie"
        else:
            db.session.add(Game(
                home_team_id=home,
                away_team_id=away,
                home_score=request.form["hs"],
                away_score=request.form["as"]
            ))
            db.session.commit()
            return redirect("/")

    return render_template_string("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <div class="container mt-5" style="max-width:600px;">
        <div class="card p-4 shadow">

            <h3>⚽ Dodaj mecz</h3>

            <form method="POST">

                <select name="home" class="form-select mb-2">
                    {% for t in teams %}
                        <option value="{{ t.id }}">{{ t.name }}</option>
                    {% endfor %}
                </select>

                <select name="away" class="form-select mb-2">
                    {% for t in teams %}
                        <option value="{{ t.id }}">{{ t.name }}</option>
                    {% endfor %}
                </select>

                <input name="hs" class="form-control mb-2" placeholder="Gole gospodarzy">
                <input name="as" class="form-control mb-2" placeholder="Gole gości">

                <button class="btn btn-success w-100">Dodaj</button>
            </form>

            <p class="text-danger">{{ error }}</p>

            <a href="/admin" class="btn btn-secondary mt-2">Powrót</a>

        </div>
    </div>
    """, teams=teams, error=error)

# ==========================================
# ADD GOALS (KRÓL STRZELCÓW)
# ==========================================

@app.route("/add_goals", methods=["GET", "POST"])
@admin_required
def add_goals():
    players = Player.query.all()

    if request.method == "POST":
        pid = request.form["player_id"]
        g = int(request.form["goals"])

        goal = Goal.query.filter_by(player_id=pid).first()

        if goal:
            goal.goals += g
        else:
            db.session.add(Goal(player_id=pid, goals=g))

        db.session.commit()
        return redirect("/admin")

    return render_template_string("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <div class="container mt-5" style="max-width:500px;">
        <div class="card p-4 shadow">

            <h3>🎯 Dodaj gole</h3>

            <form method="POST">

                <select name="player_id" class="form-select mb-2">
                    {% for p in players %}
                        <option value="{{ p.id }}">{{ p.name }}</option>
                    {% endfor %}
                </select>

                <input name="goals" type="number" class="form-control mb-2" placeholder="Gole">

                <button class="btn btn-warning w-100">Dodaj</button>
            </form>

            <a href="/admin" class="btn btn-secondary mt-2">Powrót</a>

        </div>
    </div>
    """, players=players)

# ==========================================
# HOME
# ==========================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Liga PRO</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>

<body class="bg-light">

<div class="container mt-4">

<div class="d-flex justify-content-between">
<h2>⚽ Liga PRO</h2>

<div>
<b>{{ user }}</b>
<a href="/login" class="btn btn-sm btn-primary">Login</a>
<a href="/logout" class="btn btn-sm btn-danger">Logout</a>

{% if role == "admin" %}
<a href="/admin" class="btn btn-sm btn-dark">Admin</a>
{% endif %}

</div>
</div>

<div class="card p-3 mt-3">
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

<div class="card p-3 mt-3">
<h4>⭐ Król strzelców</h4>
<b>{{ scorer.name }}</b> - {{ scorer.g }} goli
</div>

</div>

</body>
</html>
"""

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
