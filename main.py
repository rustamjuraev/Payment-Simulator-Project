import os
from flask import request
from flask import Flask, render_template, redirect, url_for, session
from flask_login import login_user, logout_user, current_user
from models import db, Users,Wallet,Transactions
from flask_bootstrap import Bootstrap5
from forms import RegisterForm,LoginForm,VerificationForm, SendMoneyForm
import flask
from utils import send_verification_code, generate_security_code
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_required
from sqlalchemy import or_,select
from flask_migrate import Migrate
from utils import generate_expiry_date,generate_card_number, generate_cvc, is_valid_name, is_valid_email
import stripe

__all__ = [Users,Wallet,Transactions]
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

endpoint_secret = os.environ.get("WEBHOOK_SECRET")

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql+psycopg2://postgres:{os.environ['POSTGRES_PASSWORD']}@localhost:5432/flask_db"
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config['WTF_CSRF_ENABLED'] = False
migrate = Migrate(app,db)
db.init_app(app)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users,int(user_id))

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
                name = session.pop("name",None)
                surname = session.pop("surname",None)
                email = session.pop("email",None)
                password = session.pop("password",None)
                new_user = Users(name=name,
                                 surname=surname,
                                 email=email,
                                 password=password)
                session.pop("security-code")
                db.session.add(new_user)
                db.session.flush()

                user_id = new_user.id
                balance = 10000
                currency = "UZS"
                card_number = generate_card_number()
                exp = generate_expiry_date()
                cvc = generate_cvc()
                new_wallet = Wallet(user_id=user_id,
                                    balance=balance,
                                    currency=currency,
                                    card_number=card_number,
                                    card_cvc=cvc,
                                    card_exp=exp)
                db.session.add(new_wallet)
                db.session.commit()
                flask.flash("Registration successful, wallet has been allocated for you!")
                return redirect(url_for("login_page"))
            except Exception as e:
                print(f"Error: {e}")

        else:
            flask.flash("Wrong verification code!")
            return redirect(url_for("register_page"))
    return render_template("verify.html",form=form)

@app.route("/login",methods=["GET","POST"])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = db.session.execute(db.select(Users).where(Users.email == email)).scalar_one_or_none()
        if user:
            if check_password_hash(user.password,password):
                security_code = generate_security_code()
                x = send_verification_code(email,security_code)
                if x != -1:
                    session["security-code"] = security_code
                    session["user-id"] = user.id
                    return redirect(url_for("verify_code"))
                else:
                    flask.flash("Failed to send the verification code, check your connection and try again")
                    return redirect(url_for("login_page"))
            else:
                flask.flash("Incorrect password, please try again")
                return redirect(url_for("login_page"))
        else:
            flask.flash("Invalid email address, register with this email first")
            return redirect(url_for("register_page"))

    return render_template("login.html", form=form)

@app.route("/verify-code", methods=["GET","POST"])
def verify_code():
    form = VerificationForm()
    if form.validate_on_submit():
        security_code = session.get("security-code")
        input_code = form.security_code.data
        if input_code == security_code:
            session.pop("security-code")
            user_id = session.get("user-id")
            user = db.session.get(Users,user_id)
            login_user(user)
            session.pop("user-id")
            return redirect(url_for("dashboard_page"))

        else:
            flask.flash("Incorrect security code, please try again! ")
            return redirect(url_for("verify_code"))

    return render_template("verify.html", form=form)


@app.route("/dashboard")
@login_required
def dashboard_page():
    """the next step is to build a dashboard page and its functionalities. It should take me to other routes to perform
    certain actions like sending money, top up balance, show card details and my transaction list if clicked"""
    user = current_user
    recent_transactions = ((select(Transactions)
                           .where(
        or_(
            Transactions.sender_id==user.wallet.id,
            Transactions.receiver_id==user.wallet.id
        )
    )
    ).order_by(Transactions.created_at.desc()).limit(4))
    recent_transactions = db.session.execute(recent_transactions).scalars().all()

    return render_template("dashboard.html", user=user, recent_transactions=recent_transactions)

@app.route("/logout")
@login_required
def logout():
    """user needs to log out from here"""
    logout_user()
    return redirect(url_for("home_page"))

@app.route("/send-money", methods=["GET","POST"])
@login_required
def send_money():
    """I need to write the logic for sending money from one account to the other and implement mutex"""
    if request.method == "POST":
        name = request.form.get("recipient_name")
        email = request.form.get("recipient_email")
        amount = request.form.get("amount", type=float)
        if not is_valid_name(name):
            flask.flash("Invalid name, please try again with a valid name")
            return redirect(url_for("send_money"))

        if not is_valid_email(email):
            flask.flash("Email address is not valid, please try again")
            return redirect(url_for("send_money"))

        sender = db.session.execute(
            db.select(Users).where(Users.id == current_user.id)).with_for_update().scalar_one_or_none()

        if sender.wallet.balance < amount:
            flask.flash("There is not enough money in your bank account to make this transaction, please top up first")
            return redirect(url_for("top_up"))

        recipient = db.session.execute(
            db.select(Users).where(Users.email == email)).with_for_update().scalar_one_or_none()
        if recipient:
            if recipient.name == name:
                """i need to write my send money logic here and handle potential exceptions"""
                try:
                    sender.wallet.balance -= amount
                    recipient.wallet.balance += amount

                    """here i need to create a transaction object and populate it and commit it """
                    sender_id = sender.id
                    receiver_id = recipient.id
                    status = "success"
                    transaction_type = "transfer"
                    new_transaction = Transactions(sender_id=sender_id,
                                                   receiver_id=receiver_id,
                                                   status=status,
                                                   amount=amount,
                                                   type=transaction_type)
                    db.session.add(new_transaction)
                    db.session.commit()

                    return redirect(url_for("dashboard_page"))

                except Exception as e:
                    print(f"Error while completing the transaction: {e}")
                    db.session.rollback()

            else:
                flask.flash(f"Names did not match on the database, did you mean: {recipient.name}")
                return redirect(url_for("send_money"))
        else:
            flask.flash("Account not found from the database, please check that you have inserted the email correctly")
            return redirect(url_for("send_money"))

    return render_template("send_money.html",user=current_user)

@app.route("/top-up",methods=["GET","POST"])
@login_required
def top_up():
    if request.method == "POST":
        amount = request.form.get("amount", type=int)
        if amount:
            amount = int(amount)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount*100,
                currency="usd",
                metadata={"user_id":current_user.id}
            )
            return render_template("stripe.html",
                                   client_secret=payment_intent.client_secret,
                                   stripe_public_key=os.environ.get("STRIPE_PUBLIC_KEY"))
        else:
            flask.flash("Invalid input given for amount, please try again")
            return render_template("top_up.html")

    return render_template("top_up.html",user=current_user)


@app.route("/webhook", methods=['POST'])
def webhook():
  print("Webhook received")
  payload = request.get_data()
  sig_header = request.headers.get("STRIPE_SIGNATURE")
  event = None
  try:
      event = stripe.Webhook.construct_event(
          payload, sig_header, endpoint_secret
      )
  except ValueError as e:
    return "Invalid payload", 400

  except stripe.error.SignatureVerificationError as e:
    return "Invalid signature", 400

  event_dict = event.to_dict()
  if event_dict['type'] == "payment_intent.succeeded":
    intent = event_dict['data']['object']
    print("Succeeded: ", intent['id'])
    """need to change balance here"""
    amount = intent["amount"]
    amount_usd = amount / 100
    amount_uzs = amount_usd * 12000
    user_id = int(intent["metadata"]["user_id"])
    user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar_one()
    try:
        print("This part of the code is being executed now ")
        user.wallet.balance += amount_uzs
        db.session.commit()
        return "Ok", 200

    except Exception as e:
        print(f"Error:{e}")
    except stripe.error.SignatureVerificationError as e:
        return '', 403  # Signature mismatch

  elif event_dict['type'] == "payment_intent.payment_failed":
    intent = event_dict['data']['object']
    error_message = intent['last_payment_error']['message'] if intent.get('last_payment_error') else None
    print("Failed: ", intent['id']), error_message

  return "OK", 200

@app.route("/see-details")
@login_required
def see_my_card():

    return render_template("card_details.html", user=current_user)

@app.route("/transactions")
@login_required
def transactions():
    user = current_user
    all_transactions = ((select(Transactions)
                           .where(
        or_(
            Transactions.sender_id==user.wallet.id,
            Transactions.receiver_id==user.wallet.id
        )
    )
    ).order_by(Transactions.created_at.desc()))
    all_transactions = db.session.execute(all_transactions).scalars().all()
    return render_template("transactions.html", transactions=all_transactions)


if __name__ == "__main__":
    app.run(debug=True)
