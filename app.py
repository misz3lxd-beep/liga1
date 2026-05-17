from flask import Flask, render_template_string
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
# BAZA + DANE
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

        g1 = Game(home_team_id=legia.id, away_team_id=lech.id, home_score=3, away_score=1)
        g2 = Game(home_team_id=wisla.id, away_team_id=legia.id, home_score=2, away_score=2)

        db.session.add_all([g1, g2])
        db.session.commit()

        db.session.add_all([
            PlayerGoal(player=p1, game=g1, goals=2),
            PlayerGoal(player=p2, game=g1, goals=1),
            PlayerGoal(player=p1, game=g2, goals=1),
            PlayerGoal(player=p3, game=g2, goals=2),
        ])

        db.session.commit()

# ==========================================
# LOGIKA
# ==========================================

def team_table():
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
            elif g.away_score == g.away_score:
                points += 1

        result.append({"team": t.name, "points": points})

    return sorted(result, key=lambda x: x["points"], reverse=True)


def best_player():
    return db.session.query(
        Player.name,
        func.sum(PlayerGoal.goals).label("goals")
    ).join(PlayerGoal).group_by(Player.id).order_by(func.sum(PlayerGoal.goals).desc()).first()


def best_vs_team(team_name):
    team = Team.query.filter_by(name=team_name).first()

    return db.session.query(
        Player.name,
        func.sum(PlayerGoal.goals).label("goals")
    ).join(PlayerGoal).join(Game).filter(
        (Game.home_team_id == team.id) | (Game.away_team_id == team.id)
    ).filter(
        Player.team_id != team.id
    ).group_by(Player.id).order_by(func.sum(PlayerGoal.goals).desc()).first()


# ==========================================
# UI (POPRAWIONE CZYTELNOŚĆ)
# ==========================================

HTML = """
<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>Liga1 Dashboard</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body {
    background: #f5f7fb;
    color: #111;
}

.title {
    text-align: center;
    font-size: 36px;
    font-weight: 800;
    margin: 30px 0;
    color: #111;
}

.card {
    border: none;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
}

.card h5 {
    font-weight: 700;
    color: #111;
}

.big-number {
    font-size: 26px;
    font-weight: 700;
    color: #16a34a;
}

table {
    color: #111;
}

th {
    background: #111 !important;
    color: white !important;
}

td {
    color: #111;
}

</style>

</head>

<body>

<div class="container">

<div class="title">⚽ Liga1 Dashboard</div>

<div class="row g-3">

    <div class="col-md-4">
        <div class="card p-3">
            <h5>🏆 Najlepsza drużyna</h5>
            <div class="big-number">
                {{ table[0].team }} — {{ table[0].points }} pkt
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card p-3">
            <h5>⭐ Najlepszy zawodnik</h5>
            <div class="big-number">
                {{ player.name }}
            </div>
            <div>{{ player.goals }} goli</div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card p-3">
            <h5>🔥 VS Legia</h5>
            <div class="big-number">
                {{ vs_player.name }}
            </div>
            <div>{{ vs_player.goals }} goli</div>
        </div>
    </div>

</div>

<div class="card mt-4 p-3">

<h5>📊 Tabela ligowa</h5>

<table class="table table-striped table-hover mt-2">

<thead>
<tr>
<th>Miejsce</th>
<th>Drużyna</th>
<th>Punkty</th>
</tr>
</thead>

<tbody>
{% for row in table %}
<tr>
<td>{{ loop.index }}</td>
<td>{{ row.team }}</td>
<td><b>{{ row.points }}</b></td>
</tr>
{% endfor %}
</tbody>

</table>

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

    table = team_table()
    player = best_player()
    vs_player = best_vs_team("Legia Warszawa")

    return render_template_string(
        HTML,
        table=table,
        player=player,
        vs_player=vs_player
    )


if __name__ == "__main__":
    app.run(debug=True)
