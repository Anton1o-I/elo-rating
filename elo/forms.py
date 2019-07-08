from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired


class ResultForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    p2_name = StringField("Player2 Name", validators=[DataRequired()])
    p1_score = StringField("Player1 Score", validators=[DataRequired()])
    p2_score = StringField("Player2 Score", validators=[DataRequired()])
    submit = SubmitField("Add Result")


class ConfirmForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    match_id = StringField("Match ID", validators=[DataRequired()])
    confirm = SelectField(
        "Status",
        choices=[("confirm", "Confirm"), ("deny", "Deny")],
        validators=[DataRequired()],
    )
    submit = SubmitField("Add Result")


class AddPlayerForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Add Result")


class RivalryForm(FlaskForm):
    player1 = StringField("Player 1", validators=[DataRequired()])
    player2 = StringField("Player 2", validators=[DataRequired()])
    submit = SubmitField("View History")
