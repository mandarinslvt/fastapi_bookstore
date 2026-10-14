from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Boolean, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Book_obj(Base):
    __tablename__ = 'Books'
    id: Mapped[int] = mapped_column (Integer, primary_key = True)
    title: Mapped[str] = mapped_column (String, nullable = False)
    author: Mapped[str] = mapped_column (String, nullable = False)
    genre: Mapped[str] = mapped_column (String, nullable = True)
    year: Mapped[int] = mapped_column (Integer, nullable = True)
    price: Mapped[int] = mapped_column(Integer, default=500, nullable=False) #price
    image_url: Mapped[str | None] = mapped_column(String, nullable=True) #file
    # isbn: Mapped[int] = mapped_column (Integer, primary_key=)

class Reader_obj(Base):
    __tablename__ = 'Readers'
    id: Mapped[int] = mapped_column (Integer, primary_key = True)
    name: Mapped[str] = mapped_column (String, nullable = False)
    second_name: Mapped[str] = mapped_column(String, nullable = False)
    age: Mapped[int] = mapped_column (Integer, nullable = True)
    email: Mapped[str] = mapped_column (String, nullable = False)
    registration_date: Mapped[datetime] = mapped_column (DateTime, default = datetime.today)
    phone: Mapped[str] = mapped_column (String, nullable = True)
    balance: Mapped[int] = mapped_column(Integer, default=50000, nullable=False)
class Cart_obj(Base):
    __tablename__ = 'Cart'
    id: Mapped[int] = mapped_column (Integer, primary_key = True)
    quantity: Mapped[int] = mapped_column (Integer, default=1, nullable = False)
    reader_id: Mapped[int] = mapped_column (Integer, ForeignKey('Readers.id'), nullable=False)
    book_id: Mapped[int] = mapped_column (Integer, ForeignKey('Books.id'), nullable=False)
    book: Mapped["Book_obj"] = relationship("Book_obj")

class Promo_obj(Base):
    __tablename__ = 'Promocodes'
    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Сам промокод, например 'SALE10'
    discount_amount: Mapped[int] = mapped_column(Integer, nullable=False) # Размер скидки в рублях
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # Активен ли он
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False) # До какого числа действует
    reader_id: Mapped[int] = mapped_column(Integer, ForeignKey('Readers.id'), nullable=True) # Кто уже применил (если одноразовый)

class Reg_obj(Base):
    __tablename__ = 'Registration'
    id: Mapped[int] = mapped_column(Integer, primary_key = True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    hash_password: Mapped[str] = mapped_column(String, nullable=False)
    user_password: Mapped[str] = mapped_column(String, nullable=False)

class Buy_obj(Base):
    __tablename__ = "Purchases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    card_number: Mapped[str | None] = mapped_column(String, nullable=True)
    reader_id: Mapped[int] = mapped_column(Integer, ForeignKey('Readers.id'), nullable=False)