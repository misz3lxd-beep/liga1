from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello world!"

if app == "main":
    app.run()

    import os
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(name)

    Inteligentne
    wykrywanie
    środowiska
    if 'WEBSITE_SITE_NAME' in os.environ:
        # Jesteśmy w chmurze Azure (Środowisko Produkcyjne)
        # Zapisujemy plik bazy w specjalnym folderze /home, który zaraz utrwalimy
        db_path = '/home/site/liga_chmurowa.db'
    else:
        # Jesteśmy na komputerze dewelopera (Lokalnie)
        db_path = 'liga_chmurowa.db'

    Konfiguracja
    połączenia
    SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(app)

    Tutaj
    zdefiniujcie
    swoje
    klasy
    z
    diagramu, np:


    class League(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)


    Utworzenie
    bazy(wywoła
    się
    automatycznie
    przy
    starcie)
    with app.app_context():
        db.create_all()

    if name == 'main':
        app.run(debug=True)
