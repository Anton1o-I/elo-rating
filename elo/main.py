from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
from elo import elo_adjust
from passlib.apps import custom_app_context as pwd_context
from flask_httpauth import HTTPBasicAuth
from pandas import DataFrame


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    "data/database.sqlite"
)
db = SQLAlchemy(app)
ma = Marshmallow(app)
auth = HTTPBasicAuth()


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    rating = db.Column(db.Integer, unique=False)
    wins = db.Column(db.Integer, unique=False)
    losses = db.Column(db.Integer, unique=False)
    password_hash = db.Column(db.String(128))

    def __init__(self, name, rating, wins, losses):
        self.name = name
        self.rating = rating
        self.wins = wins
        self.losses = losses

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class PlayerSchema(ma.Schema):
    class Meta:
        fields = ("name", "rating", "wins", "losses")


player_schema = PlayerSchema()
players_schema = PlayerSchema(many=True)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1 = db.Column(db.String(80), unique=False)
    player2 = db.Column(db.String(80), unique=False)
    p1_score = db.Column(db.Integer, unique=False)
    p2_score = db.Column(db.Integer, unique=False)
    status = db.Column(db.String(10), unique=False)

    def __init__(self, player1, player2, p1_score, p2_score):
        self.player1 = player1
        self.player2 = player2
        self.p1_score = p1_score
        self.p2_score = p2_score

class MatchSchema(ma.Schema):
    class Meta:
        fields = ("id", "player1", "player2", "p1_score", "p2_score", "status")


match_schema = MatchSchema()
matches_schema = MatchSchema(many=True)


@app.route("/player", methods=["POST"])
def add_player():
    name = request.form["name"]
    password = request.form["password"]
    try:
        _ = Player.query.filter_by(name=name).first_or_404()
    except:
        new_player = Player(name, 1600, 0, 0)
        new_player.hash_password(password)
        db.session.add(new_player)
        db.session.commit()
        return jsonify(
            status_code=200,
            status=f"success, new player {name} create with rating 1600",
        )
    return jsonify(
        status_code=400, status=f"{name} already exists, names must be unique"
    )


@app.route("/rankings", methods=["GET"])
def get_rankings():
    all_players = Player.query.all()
    result = players_schema.dump(all_players).data
    df = (
        DataFrame(result)
        .reindex(["name", "rating", "wins", "losses"], axis=1)
        .sort_values(by="rating", ascending=False)
    )
    return jsonify(df.to_dict("records"))


@app.route("/player", methods=["GET"])
def get_all():
    all_players = Player.query.all()
    result = players_schema.dump(all_players)
    return jsonify(result.data)


@app.route("/player/<name>", methods=["GET"])
def get_player(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify(result.data)


@app.route("/player-rating/<name>", methods=["GET"])
def get_rating(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify(result.data["rating"])


@app.route("/player-record/<name>", methods=["GET"])
def get_record(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify({"wins": result.data["wins"], "losses": result.data["losses"]})


@app.route("/add-result", methods=["POST"])
@auth.login_required
def add_result():
    if auth.username() != request.form["p1_name"]:
        return f"Game not posted - player1 "
    new_match = Match(
        request.form["p1_name"],
        request.form["p2_name"],
        request.form["p1_score"],
        request.form["p2_score"],
    )
    new_match.status = "pending"
    db.session.add(new_match)
    db.session.commit()
    return f"Match {new_match.id} pending approval"


@auth.verify_password
def verify_password(name, password):
    player = Player.query.filter_by(name=name).first()
    if not player or not player.verify_password(password):
        return False
    return True

@app.route("/confirm-match", methods=["GET", "POST"])
@auth.login_required
def confirm_result():
    match_id = int(request.form["id"])
    m = Match.query.filter_by(id=match_id).first_or_404()
    match = match_schema.dump(m)
    if m.player2 != auth.username():
        return f"Authenticator must be {m.player2} not {auth.username()}"
    player = Player.query.filter_by(name=m.player2).first_or_404()
    ratings = {
        "p1_current": get_rating(m.player1).get_json(),
        "p2_current": get_rating(m.player2).get_json(),
    }
    new_ratings = elo_adjust(match.data, ratings)
    for p in new_ratings:
        player = Player.query.filter_by(name=p["name"]).first_or_404()
        player.name = p["name"]
        player.rating = p["rating"]
        if p["win"] == 1:
            player.wins += 1
            player.losses = player.losses
        else:
            player.wins = player.wins
            player.losses += 1
        m.status = "confirmed"
        db.session.commit()
    return "Successfully confirmed match result"


@app.route("/remove-player/<n>", methods=["DELETE"])
def del_player(n):
    player = Player.query.filter_by(name=n).first_or_404()
    db.session.delete(player)
    db.session.commit()
    return f"{n} removed from database"


@app.route("/match-history", methods=["GET"])
def get_games():
    games = Match.query.all()
    result = matches_schema.dump(games)
    return jsonify(result.data)


@app.route("/rival-history", methods=["GET"])
def get_rival_results():
    p1 = request.form["player1"]
    p2 = request.form["player2"]
    match1 = Match.query.filter(Match.player1 == p1, Match.player2 == p2)
    match2 = Match.query.filter(Match.player1 == p2, Match.player2 == p1)
    result1 = matches_schema.dump(match1)
    result2 = matches_schema.dump(match2)
    return jsonify(result1.data, result2.data)


if __name__ == "__main__":
    if not os.path.isfile("data/database.sqlite"):
        db.create_all()
        print("Database created")
    app.run(debug=True)
