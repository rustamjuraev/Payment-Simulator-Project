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
    email = EmailField("Email",validators=[DataRequired(),Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

class VerificationForm(FlaskForm):
    security_code = StringField("Security-Code",validators=[DataRequired()])
    submit = SubmitField("Proceed")

class SendMoneyForm(FlaskForm):
    card_number = StringField("Recipient Card Number",validators=[DataRequired(), Length(min=16, max=16)])
    expiry = StringField("Expiry",validators=[DataRequired(), Length(min=5, max=5)])
    cvv = StringField("CVV",validators=[DataRequired(), Length(min=3, max=3)])
    amount = StringField("Amount",validators=[DataRequired()])
    submit = SubmitField("Send Money")