from wtforms import StringField
from wtforms.fields.simple import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf import FlaskForm

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    surname = StringField("Surname", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired(), Length(min=10)])
    Submit = SubmitField("Proceed")

class LoginForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = EmailField("Email",validators=[DataRequired(),Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

class VerificationForm(FlaskForm):
    security_code = StringField("Security-Code",validators=[DataRequired()])
    submit = SubmitField("Proceed")

