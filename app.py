from flask import Flask, render_template_string, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from functools import wraps
import os

app = Flask(__name__)

# ==========================================
# CONFIG (AZURE FIX)
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "liga1.db")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "liga1-secret-key"

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
    name = db.Column(db.String(100), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    team = db.relationship("Team")

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    away_team_id = db.Column(db.Integer, db.ForeignKey("team.id"))
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

class PlayerGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    goals = db.Column(db.Integer)

    player = db.relationship("Player")

# ==========================================
# DB INIT
# ==========================================

with app.app_context():
    db.create_all()

    if Team.query.count() == 0:
        t1 = Team(name="Legia Warszawa")
        t2 = Team(name="Lech Poznań")
        t3 = Team(name="Wisła Kraków")

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        p1 = Player(name="Kowalski", team=t1)
        p2 = Player(name="Nowak", team=t2)
        p3 = Player(name="Zieliński", team=t3)

        db.session.add_all([p1, p2, p3])
        db.session.commit()

# ==========================================
# DECORATORS
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
        points = 0

        home = Game.query.filter_by(home_team_id=t.id).all()
        away = Game.query.filter_by(away_team_id=t.id).all()

        for g in home:
            if g.home_score > g.away_score:
                points += 3
            elif g.home_score == g.away_score:
                points += 1

        for g in away:
            if g.away_score > g.home_score:
                points += 3
            elif g.away_score == g.home_score:
                points += 1

        result.append({"team": t.name, "points": points})

    return sorted(result, key=lambda x: x["points"], reverse=True)

def best_player():
    res = db.session.query(
        Player.name,
        func.sum(PlayerGoal.goals).label("goals")
    ).join(PlayerGoal).group_by(Player.id).order_by(func.sum(PlayerGoal.goals).desc()).first()

    if not res:
        return type("P", (), {"name": "-", "goals": 0})

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
            session["username"] = u
            session["role"] = USERS[u]["role"]
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
    <hr>
    admin/admin<br>
    user/user
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==========================================
# TEMPLATE
# ==========================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Liga1</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container mt-4">

<h2>⚽ Liga1</h2>

<div class="card p-3 mb-3">
Zalogowany: <b>{{ username }}</b> | Rola: <b>{{ role }}</b>
<a href="/logout" class="btn btn-danger btn-sm float-end">Logout</a>
</div>

{% if role == "admin" %}
<div class="mb-3">
<a href="/add_team" class="btn btn-primary">Dodaj drużynę</a>
<a href="/add_player" class="btn btn-success">Dodaj zawodnika</a>
<a href="/add_game" class="btn btn-warning">Dodaj mecz</a>
</div>
{% endif %}

<div class="card p-3 mb-3">
<h5>🏆 Lider</h5>

{% if table %}
<b>{{ table[0].team }}</b> - {{ table[0].points }} pkt
{% endif %}
</div>

<div class="card p-3">
<h5>Tabela</h5>
<table class="table">
<tr><th>#</th><th>Drużyna</th><th>Punkty</th></tr>
{% for r in table %}
<tr>
<td>{{ loop.index }}</td>
<td>{{ r.team }}</td>
<td>{{ r.points }}</td>
</tr>
{% endfor %}
</table>
</div>

</div>
</body>
</html>
"""

# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():
    return render_template_string(
        HTML,
        table=table(),
        player=best_player(),
        role=session.get("role", "guest"),
        username=session.get("username", "Gość")
    )

# ==========================================
# ADMIN PAGES
# ==========================================

@app.route("/add_team", methods=["GET", "POST"])
@admin_required
def add_team():
    if request.method == "POST":
        db.session.add(Team(name=request.form["name"]))
        db.session.commit()
        return redirect("/")
    return "<form method='POST'><input name='name'><button>OK</button></form>"

@app.route("/add_player", methods=["GET", "POST"])
@admin_required
def add_player():
    teams = Team.query.all()

    if request.method == "POST":
        db.session.add(Player(name=request.form["name"], team_id=request.form["team_id"]))
        db.session.commit()
        return redirect("/")

    form = "<form method='POST'><input name='name'><select name='team_id'>"
    for t in teams:
        form += f"<option value='{t.id}'>{t.name}</option>"
    form += "</select><button>OK</button></form>"
    return form

@app.route("/add_game", methods=["GET", "POST"])
@admin_required
def add_game():
    teams = Team.query.all()

    if request.method == "POST":
        db.session.add(Game(
            home_team_id=request.form["home"],
            away_team_id=request.form["away"],
            home_score=request.form["home_score"],
            away_score=request.form["away_score"]
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

    form += "<input name='home_score'><input name='away_score'>"
    form += "<button>OK</button></form>"

    return form

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run()
