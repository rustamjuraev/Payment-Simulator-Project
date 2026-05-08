from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Float, DATE
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from typing import List
from flask_login import UserMixin



class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)

class Users(UserMixin,db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True,unique=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    surname: Mapped[str] = mapped_column(String(250),nullable=False)
    email: Mapped[str] = mapped_column(String(250),nullable=False,unique=True)
    password: Mapped[str] = mapped_column(String(250),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=func.now())
    wallet: Mapped["Wallet"] = relationship(back_populates="user")

class Wallet(db.Model):
    __tablename__ = "wallet"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    balance: Mapped[float] = mapped_column(Float,nullable=False)
    currency: Mapped[str] = mapped_column(String(250),nullable=False)
    user: Mapped["Users"] = relationship(back_populates="wallet")
    card_number: Mapped[str] = mapped_column(String(250))
    card_cvc: Mapped[str] = mapped_column(String(250))
    card_exp: Mapped[str] = mapped_column(String(250))
    sent_transactions: Mapped[List["Transactions"]] = relationship(
        back_populates="sender",
        foreign_keys="[Transactions.sender_id]"
    )
    received_transactions: Mapped[List["Transactions"]] = relationship(
        back_populates="receiver",
        foreign_keys="[Transactions.receiver_id]"
    )

class Transactions(db.Model):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("wallet.id"))
    amount: Mapped[float] = mapped_column(Float,nullable=False)
    status: Mapped[str] = mapped_column(String(250),nullable=False)
    type: Mapped[str] = mapped_column(String(250),nullable=False)
    created_at: Mapped[datetime] = mapped_column(DATE,default=func.now())
    sender: Mapped["Wallet"] = relationship(back_populates="sent_transactions",foreign_keys="[Transactions.sender_id]")
    receiver: Mapped["Wallet"] = relationship(back_populates="received_transactions",foreign_keys="[Transactions.receiver_id]")