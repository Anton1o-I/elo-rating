from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import os
from elo import elo_adjust

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    basedir, "app.sqlite"
)
db = SQLAlchemy(app)
ma = Marshmallow(app)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    rating = db.Column(db.Integer, unique=False)

    def __init__(self, name, rating):
        self.name = name
        self.rating = rating


class PlayerSchema(ma.Schema):
    class Meta:
        fields = ("name", "rating")


player_schema = PlayerSchema()
players_schema = PlayerSchema(many=True)


@app.route("/player", methods=["POST"])
def add_player():
    name = request.form["name"]
    try:
        player = Player.query.filter_by(name=name).first_or_404()
    except:
        new_player = Player(name, 1600)
        db.session.add(new_player)
        db.session.commit()
        return jsonify(
            status_code=200,
            status=f"success, new player {name} create with rating 1600",
        )
    return jsonify(
        status_code=400, status=f"{name} already exists, names must be unique"
    )


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


@app.route("/update-ratings", methods=["POST"])
def update_rating():
    ratings = {
        "p1_current": get_rating(request.form["p1_name"]).get_json(),
        "p2_current": get_rating(request.form["p2_name"]).get_json(),
    }

    new_ratings = elo_adjust(request.form, ratings)
    for p in new_ratings:
        player = Player.query.filter_by(name=p["name"]).first_or_404()
        player.name = p["name"]
        player.rating = p["rating"]
        db.session.commit()
    return f"Players update - {new_ratings}"


@app.route("/remove-player/<n>", methods=["DELETE"])
def del_player(n):
    player = Player.query.filter_by(name=n).first_or_404()
    db.session.delete(player)
    db.session.commit()
    return f"{n} removed from database"


if __name__ == "__main__":
    app.run(debug=True)
