from flask import Flask, render_template_string, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///liga1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# MODELE
# ==========================================

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team')

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    home_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)

class PlayerGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    goals = db.Column(db.Integer)

    player = db.relationship('Player')
    game = db.relationship('Game')

# ==========================================
# BAZA + DANE STARTOWE
# ==========================================

with app.app_context():
    db.create_all()

    if Team.query.count() == 0:

        legia = Team(name="Legia Warszawa")
        lech = Team(name="Lech Poznań")
        wisla = Team(name="Wisła Kraków")

        db.session.add_all([legia, lech, wisla])
        db.session.commit()

        p1 = Player(name="Kowalski", team=legia)
        p2 = Player(name="Nowak", team=lech)
        p3 = Player(name="Zieliński", team=wisla)

        db.session.add_all([p1, p2, p3])
        db.session.commit()

# ==========================================
# LOGIKA LIGI
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

    return db.session.query(
        Player.name,
        func.sum(PlayerGoal.goals).label("goals")
    ).join(PlayerGoal).group_by(Player.id).order_by(func.sum(PlayerGoal.goals).desc()).first()

# ==========================================
# UI
# ==========================================

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Liga1 Admin Panel</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>
body { background:#f5f7fb; }
.card { border-radius:15px; box-shadow:0 5px 20px rgba(0,0,0,0.1); }
.title { text-align:center; font-size:34px; font-weight:800; margin:20px; }
</style>
</head>

<body>

<div class="container">

<div class="title">⚽ Liga1 – Panel Admina</div>

<!-- MENU -->
<div class="row mb-3">

<div class="col">
<a href="/" class="btn btn-dark w-100">Dashboard</a>
</div>

<div class="col">
<a href="/add_team" class="btn btn-primary w-100">Dodaj drużynę</a>
</div>

<div class="col">
<a href="/add_player" class="btn btn-success w-100">Dodaj zawodnika</a>
</div>

<div class="col">
<a href="/add_game" class="btn btn-warning w-100">Dodaj mecz</a>
</div>

</div>

<!-- TOP -->
<div class="row">

<div class="col-md-4">
<div class="card p-3">
<h5>🏆 Lider</h5>
<b>{{ table[0].team }}</b><br>
{{ table[0].points }} pkt
</div>
</div>

<div class="col-md-4">
<div class="card p-3">
<h5>⭐ Najlepszy zawodnik</h5>
<b>{{ player.name }}</b><br>
{{ player.goals }} goli
</div>
</div>

</div>

<!-- TABELA -->
<div class="card mt-4 p-3">

<h5>Tabela</h5>

<table class="table table-striped">

<tr><th>Miejsce</th><th>Drużyna</th><th>Punkty</th></tr>

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
# DASHBOARD
# ==========================================

@app.route("/")
def home():
    return render_template_string(
        HTML,
        table=table(),
        player=best_player()
    )

# ==========================================
# DODAWANIE DRUŻYNY
# ==========================================

@app.route("/add_team", methods=["GET","POST"])
def add_team():

    if request.method == "POST":
        db.session.add(Team(name=request.form["name"]))
        db.session.commit()
        return redirect("/")

    return """
    <h2>Dodaj drużynę</h2>
    <form method="POST">
        <input name="name" placeholder="Nazwa">
        <button>Dodaj</button>
    </form>
    """

# ==========================================
# DODAWANIE ZAWODNIKA
# ==========================================

@app.route("/add_player", methods=["GET","POST"])
def add_player():

    teams = Team.query.all()

    if request.method == "POST":
        db.session.add(Player(
            name=request.form["name"],
            team_id=request.form["team_id"]
        ))
        db.session.commit()
        return redirect("/")

    form = """
    <h2>Dodaj zawodnika</h2>
    <form method="POST">
        <input name="name" placeholder="Imię">

        <select name="team_id">
    """

    for t in teams:
        form += f'<option value="{t.id}">{t.name}</option>'

    form += """
        </select>

        <button>Dodaj</button>
    </form>
    """

    return form

# ==========================================
# DODAWANIE MECZU
# ==========================================

@app.route("/add_game", methods=["GET","POST"])
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

    form = """
    <h2>Dodaj mecz</h2>

    <form method="POST">

    <select name="home">
    """

    for t in teams:
        form += f'<option value="{t.id}">{t.name}</option>'

    form += """
    </select>

    <select name="away">
    """

    for t in teams:
        form += f'<option value="{t.id}">{t.name}</option>'

    form += """
    </select>

    <input name="home_score" placeholder="Gole dom">
    <input name="away_score" placeholder="Gole wyjazd">

    <button>Dodaj</button>
    </form>
    """

    return form

# ==========================================
# START
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
