from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    SelectMultipleField,
    widgets,
)
from wtforms.validators import DataRequired, Length


class ResultForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(1, 20)])
    password = PasswordField("Password", validators=[DataRequired()])
    p2_name = SelectField("Player2 Name", validators=[DataRequired()])
    p1_score = StringField("Player1 Score", validators=[DataRequired()])
    p2_score = StringField("Player2 Score", validators=[DataRequired()])
    submit = SubmitField("Add Result")

    def __init__(self, players):
        super(ResultForm, self).__init__()
        self.p2_name.choices = [(n["name"], n["name"]) for n in players]


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget()
    option_widget = widgets.CheckboxInput()


class ConfirmForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    match_id = MultiCheckboxField("Match ID", validators=[DataRequired()])
    confirm = SelectField("Status", choices=[("confirm", "Confirm"), ("deny", "Deny")])
    submit = SubmitField("Add Result")

    def __init__(self, matches):
        super(ConfirmForm, self).__init__()
        self.match_id.choices = [(i, f"MatchID:{i}") for i in matches]


class AddPlayerForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Add Result")


class RivalryForm(FlaskForm):
    player1 = StringField("Player 1", validators=[DataRequired()])
    player2 = StringField("Player 2", validators=[DataRequired()])
    submit = SubmitField("View History")
