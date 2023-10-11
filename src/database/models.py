from datetime import date

from sqlalchemy import Boolean, ForeignKey, Integer, String, func

from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connect import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    login: Mapped[str] = mapped_column(String(50))
    registration_date: Mapped[date] = mapped_column(default=func.now())
    credits: Mapped[list["Credit"]] = relationship("Credit", back_populates="user")


class Dictionary(Base):
    __tablename__ = "dictionary"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50, collation="utf8mb4_general_ci"))


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[date] = mapped_column(default=func.now("%d.%m.%Y"))
    sum: Mapped[int] = mapped_column(Integer)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dictionary.id"), nullable=False
    )
    category: Mapped["Dictionary"] = relationship("Dictionary", backref="plans")


class Credit(Base):
    __tablename__ = "credits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    user: Mapped["User"] = relationship("User", back_populates="credits")
    issuance_date: Mapped[date] = mapped_column()
    return_date: Mapped[date] = mapped_column()
    actual_return_date: Mapped[date] = mapped_column(nullable=True, default=None)
    body: Mapped[int] = mapped_column(Integer)
    percent: Mapped[int] = mapped_column(Integer)


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("credits.id"), nullable=False
    )
    credits: Mapped["Credit"] = relationship("Credit", backref="payments")
    payment_date: Mapped[date] = mapped_column()
    type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dictionary.id"), nullable=False
    )
    dictionary: Mapped["Dictionary"] = relationship("Dictionary", backref="payments")
    sum: Mapped[float] = mapped_column()
