import os
from flask import Flask, render_template, redirect, url_for, session
from models import db, Users,Wallet,Transactions
from flask_bootstrap import Bootstrap5
from forms import RegisterForm,LoginForm,VerificationForm
import flask
from utils import send_verification_code, generate_security_code
from werkzeug.security import generate_password_hash, check_password_hash


__all__ = [Users,Wallet,Transactions]

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://postgres:{os.environ['POSTGRES_PASSWORD']}@localhost:5432/flask_db"
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
db.init_app(app)
with app.app_context():
    db.create_all()

""" First i need to go through the user authentication system as quickly as possible """


@app.route("/")
def home_page():
    """later add a statement saying please register or login to use and application! """
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        surname = form.surname.data
        email = form.email.data
        password = form.password.data
        hashed_password = generate_password_hash(password,"pbkdf2",salt_length=16)
        user = db.session.execute(db.select(Users).where(Users.email == email)).scalar_one_or_none()
        if user:
            flask.flash("This email already exists in the database, head over to login page")
            return redirect(url_for("home_page"))
        security_code = generate_security_code()
        value = send_verification_code(email,security_code)
        if value != -1:
            session["security-code"] = security_code
            session["name"] = name
            session["surname"] = surname
            session["email"] = email
            session["password"] = hashed_password
            return redirect(url_for("verify_email"))
    return render_template("register.html", form=form)

@app.route("/verify-email",methods=["GET","POST"])
def verify_email():
    form = VerificationForm()
    if form.validate_on_submit():
        code_input = form.security_code.data
        code = session.get("security-code")
        if code == code_input:
            try:
                name = session.pop("name")
                surname = session.pop("surname")
                email = session.pop("email")
                password = session.pop("password")
                new_user = Users(name=name,
                                 surname=surname,
                                 email=email,
                                 password=password)
                session.pop("security-code")
                db.session.add(new_user)
                db.session.commit()
                flask.flash("Registration successful!")
                return redirect(url_for("login_page"))
            except Exception as e:
                print(f"Error: {e}")

        else:
            flask.flash("Wrong verification code!")
            redirect(url_for("register_page"))
    return render_template("verify.html",form=form)

@app.route("/login")
def login_page():
    form = LoginForm()
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    """user needs to log out from here"""
    return redirect(url_for("home_page"))

if __name__ == "__main__":
    app.run(debug=True)
