from datetime import datetime, date
from sqlalchemy import String, Integer, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User_obj(Base):
    __tablename__ = 'Users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)            
    role: Mapped[str] = mapped_column(String, default='client', nullable=False) # 'client', 'seller', 'admin'
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    second_name: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=50000, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    registration_date: Mapped[date] = mapped_column(Date, default=date.today)

class Product_obj(Base):
    __tablename__ = 'Products'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    
    # --- НОВЫЕ ПОЛЯ ДЛЯ КАТЕГОРИЗАЦИИ И СКЛАДА ---
    product_type: Mapped[str] = mapped_column(String, default='книга', nullable=False) # 'книга', 'аксессуары', 'закладки', 'письменные принадлежности'
    genre: Mapped[str | None] = mapped_column(String, nullable=True) # Жанр (только для книг)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=10, nullable=False) # Количество на складе
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False) # False = "удален" продавцом (скрыт из каталога, но сохранен в БД)
    
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    preview_text: Mapped[str | None] = mapped_column(Text, nullable=True) # Первые 5-10 страниц или ознакомительный текст
    
    seller_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('Users.id'), nullable=True) 
    seller = relationship("User_obj", foreign_keys=[seller_id])

    @property
    def is_available(self) -> bool:
        """Динамический статус наличия товара"""
        return self.is_active and self.stock_quantity > 0

class Cart_obj(Base):
    __tablename__ = 'Cart'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reader_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'), nullable=False)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey('Products.id'), nullable=False)
    book: Mapped["Product_obj"] = relationship("Product_obj")

# --- НОВАЯ МОДЕЛЬ ДЛЯ ИЗБРАННОГО ---
class Favorite_obj(Base):
    __tablename__ = 'Favorites'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('Products.id'), nullable=False)
    
    product: Mapped["Product_obj"] = relationship("Product_obj")
    user = relationship("User_obj")

class Promo_obj(Base):
    __tablename__ = 'Promocodes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    discount_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reader_id: Mapped[int | None] = mapped_column(Integer, ForeignKey('Users.id'), nullable=True)

class Buy_obj(Base):
    __tablename__ = "Purchases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    card_number: Mapped[str | None] = mapped_column(String, nullable=True)
    
    reader_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'), nullable=False) 
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey('Products.id'), nullable=False) 
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey('Users.id'), nullable=False) 
    
    product = relationship("Product_obj")
    reader = relationship("User_obj", foreign_keys=[reader_id])
    seller = relationship("User_obj", foreign_keys=[seller_id])