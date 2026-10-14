from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Base, Book_obj, Reader_obj, Cart_obj, Promo_obj, Reg_obj, Buy_obj
from fastapi import FastAPI, Request, Form, Depends, HTTPException 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi import status
from database import engine, SessionLocal
from datetime import datetime
from pydantic import BaseModel

app = FastAPI()
Base.metadata.create_all(bind=engine)
app.mount("/static", StaticFiles(directory="styles"), name="static")
templates = Jinja2Templates (directory = "templates")

class PromoCheck(BaseModel):
    code_input: str
    cart_total: int

class UserCreate(BaseModel):
    email: str
    password: str

class CardChoice(BaseModel):
    cvc: str
    name: str
    date: str

class PurchaseFunc(BaseModel):
    reader_id: int
    card_number: str | None = None # заполнить или оставить пустой


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/')
def read_root(request: Request, db: Session = Depends(get_db)):
    # вытаскиваем все книги из базы данных
    query = select(Book_obj)
    books = db.execute(query).scalars().all()

    return templates.TemplateResponse(
        request=request, 
        name='index.html', 
        context={'books': books}
    )

@app.get('/books_obj')
def books_root(db: Session = Depends(get_db)):
    query = select(Book_obj)
    books = db.execute(query).scalars().all()
    return {'Book-list': books}

@app.get('/readers_obj')
def readers_root(db: Session = Depends(get_db)):
    query = select(Reader_obj)
    readers = db.execute(query).scalars().all()
    return{'Readers-list': readers}

@app.get('/book/{book_id}')
async def book_model(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book_obj, book_id)
    if not book:
        raise HTTPException(status_code=404, detail='Книга не найдена в магазине')
    return{'Book_models': book}

@app.get('/reader/{reader_id}')
async def reader_model(reader_id: int, db: Session = Depends(get_db)):
    reader = db.get(Reader_obj, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail='User not found')
    return{'Reader_models': reader}

@app.get('/profile/{reader_id}')
async def get_profile(reader_id: int, request: Request, db: Session = Depends(get_db)):
    user = db.get(Reader_obj, reader_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found!')

    return templates.TemplateResponse(
        request = request,
        name = 'profile.html',
        context = {'user': user}
    )

@app.get('/cart')
def get_cart(request: Request, reader_id: int, db: Session = Depends(get_db)):
    query = select(Cart_obj).where(Cart_obj.reader_id == reader_id)
    cart_items = db.execute(query).scalars().all()
    
    total_price = 0
    for item in cart_items:
        total_price += item.book.price * item.quantity

    reader = db.get(Reader_obj, reader_id)
    return templates.TemplateResponse(
        request=request, 
        name='cart.html', 
        context={
            'cart_items': cart_items,
            'total_price': total_price,
            'reader': reader,
        }
    )

@app.post('/cart/add')
async def add_cart(book_id: int, reader_id: int, db: Session = Depends(get_db)):
    search_book = db.get(Book_obj, book_id)
    if not search_book:
        raise HTTPException(status_code=404, detail='Book not found!')
    
    search_reader = db.get(Reader_obj, reader_id)
    if not search_reader:
        raise HTTPException(status_code=404, detail='User not found!')
        
    new_item = Cart_obj(book_id=book_id, reader_id=reader_id, quantity=1)
    db.add(new_item)
    db.commit()
    
    return RedirectResponse(
        url=f"/cart?reader_id={reader_id}", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.post('/cart/promo')
async def input_promo(
    code_input: str = Form(...),
    cart_total: int = Form(...),
    db: Session = Depends(get_db)
):
    code_upper = code_input.upper()
    
    query = select(Promo_obj).where(Promo_obj.code == code_upper)
    promo = db.execute(query).scalars().first()
    
    if not promo:
        raise HTTPException(status_code=404, detail='Промокод не найден')

    if not promo.active:
        raise HTTPException(status_code=400, detail='Промокод недействителен')
    
    if datetime.now() > promo.expires_at:
        raise HTTPException(status_code=400, detail='Срок действия промокода истек')
    
    discount = promo.discount_amount
    
    if discount > cart_total:
        discount = cart_total
        
    new_total = cart_total - discount
    
    return {
        "status": "success",
        "code": code_upper,
        "discount": discount,
        "new_total": cart_total - discount
    }

@app.post('/registr/user')
def reg_user(user: UserCreate, db: Session = Depends(get_db)):
    query = select(Reg_obj).where(Reg_obj.email == user.email)
    getting_user = db.execute(query).scalars().first()

    if getting_user:
        raise HTTPException(status_code=400, detail='Такой пользователь уже существует.')
    
    new_user = Reg_obj(
        email=user.email,
        user_password=user.password,
        hash_password=user.password + 'hash'
    )
    db.add(new_user)
    db.commit()
    return {'status': 'succes', 'message': 'Ready!'}

@app.post('/cart/delete/{item_id}')
async def delete_cart_item(item_id: int, db: Session = Depends(get_db)):
    cart_item = db.get(Cart_obj, item_id)
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Элемент корзины не найден")
    
    #запоминаем reader_id, чтобы после удаления вернуть пользователя именно в его корзину
    reader_id = cart_item.reader_id
    
    #удаляем элемент из базы данных и сохраняем изменения
    db.delete(cart_item)
    db.commit()
    
    #перенаправляем пользователя обратно в корзину
    return RedirectResponse(
        url=f"/cart?reader_id={reader_id}", 
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.post('/purchase')
async def buy_func(
    reader_id: int = Form(...), 
    db: Session = Depends(get_db)
):
    reader = db.get(Reader_obj, reader_id)
    if not reader:
        raise HTTPException(status_code=404, detail='Пользователь не найден!')
        
    # берём реальный баланс из базы данных читателя
    amount_balance = reader.balance 

    query = select(Cart_obj).where(Cart_obj.reader_id == reader_id)
    cart_items = db.execute(query).scalars().all()

    # проверка на пустую корзину
    if not cart_items:
        raise HTTPException(status_code=400, detail='Ваша корзина пуста!')
    
    total_price = 0
    for item in cart_items:
        total_price += item.book.price * item.quantity

    # проверка нехватки средств. В базе данных по умолчанию присутствует сумма
    if amount_balance < total_price:
        raise HTTPException(
            status_code=400, 
            detail=f'Недостаточно средств! К оплате: {total_price} ₽, ваш баланс: {amount_balance} ₽'
        )

    reader.balance -= total_price 

    new_purchase = Buy_obj(
        total_price = total_price,
        reader_id = reader_id
    )
    db.add(new_purchase)

    for item in cart_items:
        db.delete(item)

    db.commit()
    
    return {
        "status": "success",
        "redirect": "/purchase/success"
    }

@app.get('/purchase/success')
def cat_success(request: Request):
    return templates.TemplateResponse(request=request, name='success.html')