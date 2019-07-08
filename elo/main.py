from flask import Flask, request, jsonify, render_template, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from forms import AddPlayerForm, ConfirmForm, ResultForm, RivalryForm
import os
from elo import elo_adjust
from passlib.apps import custom_app_context as pwd_context
from flask_httpauth import HTTPBasicAuth
from pandas import DataFrame
from config import Config


app = Flask(__name__)
app.config.from_object(Config)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    "data/database.sqlite"
)
db = SQLAlchemy(app)
ma = Marshmallow(app)
auth = HTTPBasicAuth()

# Player schema for sqlite database
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

    # method to create a password hash
    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    # method to verify a password for the Person object
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)


class PlayerSchema(ma.Schema):
    class Meta:
        fields = ("name", "rating", "wins", "losses")


player_schema = PlayerSchema()
players_schema = PlayerSchema(many=True)


# Match schema for storing state of a match
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


@auth.verify_password
def verify_password(name, password):
    player = Player.query.filter_by(name=name).first()
    if not player or not player.verify_password(password):
        return False
    return True


# add_player will add a player to the player table and hash their password
# for future auth
@app.route("/add-player", methods=["GET", "POST"])
def add_player():
    form = AddPlayerForm()
    if form.validate_on_submit():
        try:
            _ = Player.query.filter_by(name=request.form["username"]).first_or_404()
        except:
            new_player = Player(request.form["username"], 1600, 0, 0)
            new_player.hash_password(request.form["password"])
            db.session.add(new_player)
            db.session.commit()
            flash(
                "Player {} added with an elo rating of 1600".format(
                    request.form["username"]
                )
            )
            return redirect("/rankings")
    return render_template("add-player.html", title="Add Player", form=form)


# get_rankings will return the rankings in order for all players
@app.route("/rankings", methods=["GET"])
def get_rankings():
    all_players = Player.query.all()
    result = players_schema.dump(all_players).data
    df = (
        DataFrame(result)
        .reindex(["name", "rating", "wins", "losses"], axis=1)
        .sort_values(by="rating", ascending=False)
    )
    rankings = df.to_dict("records")
    return render_template("rankings.html", len=len(rankings), rankings=rankings)


# get_all queries the database and returns all the players in the database unordered
@app.route("/player", methods=["GET"])
def get_all():
    all_players = Player.query.all()
    result = players_schema.dump(all_players)
    return jsonify(result.data)


# get_player will query for a specific player and return their current state
@app.route("/player/<name>", methods=["GET"])
def get_player(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify(result.data)


# get_rating will get the current rating for a single player
@app.route("/player-rating/<name>", methods=["GET"])
def get_rating(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify(result.data["rating"])


# get_record will return the win/loss record for a single player
@app.route("/player-record/<name>", methods=["GET"])
def get_record(name):
    player = Player.query.filter_by(name=name).first_or_404()
    result = player_schema.dump(player)
    return jsonify({"wins": result.data["wins"], "losses": result.data["losses"]})


# add_result will add the results of a match to the database with a status of "pending"
# p1_score needs to match score for the person entering the game result
@app.route("/add-match", methods=["GET", "POST"])
def add_result():
    form = ResultForm()
    if form.validate_on_submit():
        p = Player.query.filter_by(name=request.form["username"]).first_or_404()
        if p.verify_password(request.form["password"]):
            new_match = Match(
                request.form["username"],
                request.form["p2_name"],
                request.form["p1_score"],
                request.form["p2_score"],
            )
            new_match.status = "pending"
            db.session.add(new_match)
            db.session.commit()
            return redirect("/rankings")
        else:
            return jsonify("Authentication error", status_code=401)
    return render_template("add-result.html", title="Add Match Result", form=form)


# confirm_result provides two party auth to ensure that both parties sign off
# on the result of a match.
@app.route("/confirm-match", methods=["GET", "POST"])
def confirm_result():
    d = get_pending()
    form = ConfirmForm()
    if form.validate_on_submit():
        p = Player.query.filter_by(name=request.form["username"]).first_or_404()
        if p.verify_password(form.password.data):
            m = Match.query.filter(Match.id == form.match_id.data).first_or_404()
            match = match_schema.dump(m).data
            if m.status == "confirmed":
                return f"Match already confirmed"
            if m.player2 != request.form["username"]:
                return f"Authenticator must be {m.player2} not {form.username.data}"
            if request.form["confirm"] == "deny":
                m.status = "denied"
                db.session.commit()
                return redirect("/confirm-match")
            ratings = {
                "p1_current": get_rating(m.player1).get_json(),
                "p2_current": get_rating(m.player2).get_json(),
            }
            new_ratings = elo_adjust(match, ratings)
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
                db.session.commit()
            m.status = "confirmed"
            db.session.commit()
            return redirect(f"/confirm-match")
    return render_template(
        "confirm-result.html", title="Confirm Match Result", form=form, matches=d
    )


# del_player will delete the specified player from the db.
@app.route("/remove-player/<n>", methods=["GET", "DELETE"])
def del_player(n):
    player = Player.query.filter_by(name=n).first_or_404()
    db.session.delete(player)
    db.session.commit()
    return f"{n} removed from database"


# get_confirmed returns all of the games that have occured in the database
@app.route("/match-history", methods=["GET"])
def get_confirmed():
    games = Match.query.filter(Match.status == "confirmed")
    result = matches_schema.dump(games)
    return render_template("match-history.html", matches=result.data)


# get_pending returns the list of games that have not yet been confirmed/denied
def get_pending():
    games = Match.query.filter(Match.status == "pending")
    result = matches_schema.dump(games)
    return result.data


@app.route("/")
def home():
    return redirect("/rankings")


# get_rival_results aggregates the history of two players matches against
# eachother.
@app.route("/rival-history", methods=["GET", "POST"])
def get_rival_results():
    form = RivalryForm()
    if form.validate_on_submit():
        p1 = request.form["player1"]
        p2 = request.form["player2"]
        match1 = Match.query.filter(
            (
                (Match.player1 == p1)
                & (Match.player2 == p2)
                & (Match.status == "confirmed")
            )
            | (
                (Match.player1 == p2)
                & (Match.player2 == p1)
                & (Match.status == "confirmed")
            )
        )
        results = matches_schema.dump(match1).data
        empty = {"wins": 0, "losses": 0}
        keys = [p1, p2]
        p_dict = {key: empty.copy() for key in keys}
        for i in results:
            if i["p1_score"] > i["p2_score"]:
                p_dict[i["player1"]]["wins"] += 1
                p_dict[i["player2"]]["losses"] += 1
            elif i["p1_score"] < i["p2_score"]:
                p_dict[i["player2"]]["wins"] += 1
                p_dict[i["player1"]]["losses"] += 1
        return render_template(
            "rival-history.html", form=form, matches=results, summary=p_dict
        )
    return render_template("rival-history.html", form=form, summary=dict())


if __name__ == "__main__":
    if not os.path.isfile("data/database.sqlite"):
        db.create_all()
        print("Database created")
    app.run(debug=True)
