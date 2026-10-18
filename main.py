from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from models import Base, Product_obj, User_obj, Cart_obj, Promo_obj, Buy_obj, Favorite_obj
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie, Response, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from database import engine, SessionLocal
from datetime import datetime

app = FastAPI()
Base.metadata.create_all(bind=engine)

# Подключение статики и шаблонов
app.mount("/static", StaticFiles(directory="styles"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(cookie_user_id: str | None = Cookie(None, alias="user_id"), db: Session = Depends(get_db)):
    if not cookie_user_id:
        return None
    return db.get(User_obj, int(cookie_user_id))

# - - -

@app.get('/')
def read_root(
    request: Request, 
    search: str | None = None, 
    product_type: str | None = None,
    genre: str | None = None,
    db: Session = Depends(get_db),
    current_user: User_obj = Depends(get_current_user)
):
    # Показываем только активные товары (не удаленные)
    query = select(Product_obj).where(Product_obj.is_active == True)
    
    if search:
        query = query.where(
            or_(
                Product_obj.title.ilike(f"%{search}%"),
                Product_obj.author.ilike(f"%{search}%"),
                Product_obj.genre.ilike(f"%{search}%")
            )
        )
    if product_type:
        query = query.where(Product_obj.product_type == product_type)
    if genre:
        query = query.where(Product_obj.genre == genre)
        
    books = db.execute(query).scalars().all()

    return templates.TemplateResponse(
        request=request, 
        name='index.html',
        context={'books': books, 'user': current_user, 'search': search, 'product_type': product_type, 'genre': genre}
    )

from fastapi.responses import Response

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    # Возвращаем пустой ответ с правильным статус-кодом, чтобы браузер отстал
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# API для динамического (живого) поиска через JS fetch()
@app.get('/api/search')
async def api_search(search: str | None = None, db: Session = Depends(get_db)):
    query = select(Product_obj).where(Product_obj.is_active == True)
    if search:
        query = query.where(
            or_(
                Product_obj.title.ilike(f"%{search}%"),
                Product_obj.author.ilike(f"%{search}%")
            )
        )
    products = db.execute(query).scalars().all()
    return [{
        "id": p.id,
        "title": p.title,
        "author": p.author,
        "price": p.price,
        "image_url": p.image_url,
        "stock_quantity": p.stock_quantity
    } for p in products]


# - - -

@app.post('/register')
async def register_user(
    username: str = Form(...), password: str = Form(...),
    name: str = Form(...), second_name: str = Form(...),
    email: str = Form(...), role: str = Form('client'),
    db: Session = Depends(get_db)
):
    existing_user = db.execute(select(User_obj).where(User_obj.username == username)).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Пользователь с таким логином уже существует')
        
    new_user = User_obj(
        username=username, password=password, role=role,
        name=name, email=email, second_name=second_name
    )
    db.add(new_user)
    db.commit()

    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key='user_id', value=str(new_user.id), httponly=True)
    return response

# - - -

@app.get('/login')
async def login_page(
    request: Request, 
    current_user: User_obj = Depends(get_current_user)
    ):
    # Если пользователь уже авторизован, отправляем его на главную
    if current_user:
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
        
    # Иначе открываем созданную страницу login.html
    return templates.TemplateResponse(
        request=request, 
        name='login.html', 
        context={'user': current_user}
    )


# - - -
@app.post('/login')
async def login_user(
    request: Request,
    username_input: str = Form(...),       
    password_input: str = Form(...),        
    db: Session = Depends(get_db)
):
    # Ищем пользователя в базе данных
    query = select(User_obj).where(User_obj.username == username_input)
    user = db.execute(query).scalars().first()
    
    if not user or user.password != password_input:
        return templates.TemplateResponse(
            request=request, 
            name='login.html', 
            context={
                'user': None, 
                'error': "Неверный логин или пароль", 
                'entered_username': username_input
            }
        )
    
    res = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    res.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return res

@app.get('/logout')
async def logout_user():
    response = RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key='user_id')
    return response


# --- ПРОФИЛЬ И ДЕТАЛИ ---

@app.get('/profile/{user_id}')
async def get_profile(user_id: int, request: Request, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user or current_user.id != user_id:
        return RedirectResponse(url='/')

    # Загружаем историю покупок
    history_query = select(Buy_obj).where(Buy_obj.reader_id == user_id)
    purchases = db.execute(history_query).scalars().all()

    return templates.TemplateResponse(
        request=request,
        name='profile.html',
        context={'user': current_user, 'purchases': purchases}
    )

@app.get('/book/{book_id}/read')
async def read_book_preview(book_id: int, request: Request, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.get(Product_obj, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Книга не найдена в магазине")
        
    return templates.TemplateResponse(
        request=request, 
        name='read.html', 
        context={'book': book, 'user': current_user}
    )


# --- КОРЗИНА И ИЗБРАННОЕ (ДИНАМИЧЕСКИЕ ЧЕРЕЗ JSON/AJAX) ---

@app.get('/favorites')
async def get_favorites_page(
    request: Request, 
    current_user: User_obj = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    # Загружаем связи избранного для текущего пользователя
    query = select(Favorite_obj).where(Favorite_obj.user_id == current_user.id)
    fav_items = db.execute(query).scalars().all()
    
    # Достаем из связей объекты самих продуктов (книг, закладок)
    books = [item.product for item in fav_items if item.product is not None]

    return templates.TemplateResponse(
        request=request, 
        name='favorites.html', 
        context={'books': books, 'user': current_user}
    )

@app.get('/cart')
def get_cart(request: Request, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    query = select(Cart_obj).where(Cart_obj.reader_id == current_user.id)
    cart_items = db.execute(query).scalars().all()
    
    total_price = sum(item.book.price * item.quantity for item in cart_items)

    return templates.TemplateResponse(
        request=request, 
        name='cart.html', 
        context={'cart_items': cart_items, 'total_price': total_price, 'user': current_user}
    )

@app.post('/cart/add')
async def add_cart(book_id: int, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return JSONResponse(status_code=401, content={'status': 'error', 'message': 'Пожалуйста, войдите в аккаунт!'})

    book = db.get(Product_obj, book_id)
    if not book or not book.is_active or book.stock_quantity <= 0:
        return JSONResponse(status_code=400, content={'status': 'error', 'message': 'Товара нет в наличии!'})
    
    # Проверяем, есть ли уже товар в корзине
    existing = db.execute(select(Cart_obj).where(Cart_obj.reader_id == current_user.id, Cart_obj.book_id == book_id)).scalars().first()
    if existing:
        existing.quantity += 1
    else:
        new_item = Cart_obj(book_id=book_id, reader_id=current_user.id, quantity=1)
        db.add(new_item)
        
    db.commit()
    return {'status': 'success', 'message': 'Товар добавлен в корзину!'}

@app.post('/cart/delete/{item_id}')
async def delete_cart_item(item_id: int, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
         raise HTTPException(status_code=401)
    cart_item = db.get(Cart_obj, item_id)
    if cart_item and cart_item.reader_id == current_user.id:
        db.delete(cart_item)
        db.commit()
    return RedirectResponse(url='/cart', status_code=status.HTTP_303_SEE_OTHER)

# Избранное (Добавить/Удалить динамически)
@app.post('/favorite/toggle/{product_id}')
async def toggle_favorite(product_id: int, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return JSONResponse(status_code=401, content={'status': 'error', 'message': 'Необходима авторизация'})
        
    query = select(Favorite_obj).where(Favorite_obj.user_id == current_user.id, Favorite_obj.product_id == product_id)
    fav = db.execute(query).scalars().first()
    
    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removed", "message": "Удалено из избранного"}
    else:
        new_fav = Favorite_obj(user_id=current_user.id, product_id=product_id)
        db.add(new_fav)
        db.commit()
        return {"status": "added", "message": "Добавлено в избранное"}


# --- ОФОРМЛЕНИЕ ЗАКАЗА (ПОКУПКА) ---

# --- ОФОРМЛЕНИЕ ЗАКАЗА (ПОКУПКА) ---

@app.post('/purchase')
async def buy_func(current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Войдите в аккаунт")

    cart_items = db.execute(select(Cart_obj).where(Cart_obj.reader_id == current_user.id)).scalars().all()
    if not cart_items:
        raise HTTPException(status_code=400, detail='Ваша корзина пуста!')
    
    total_price = sum(item.book.price * item.quantity for item in cart_items)

    if current_user.balance < total_price:
        raise HTTPException(status_code=400, detail=f'Недостаточно средств!')

    # Списываем баланс покупателя
    current_user.balance -= total_price 

    # Обрабатываем КАЖДЫЙ товар в корзине отдельно
    for item in cart_items:
        product = item.book
        
        # Проверка остатка на складе
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Товара '{product.title}' нет в нужном количестве!")
            
        # Уменьшаем количество на складе
        product.stock_quantity -= item.quantity
        
        # Начисляем деньги продавцу
        if product.seller_id:
            seller = db.get(User_obj, product.seller_id)
            if seller:
                seller.balance += product.price * item.quantity
                
        # Создаем запись о покупке (сохраняются ВСЕ товары внутри цикла)
        new_purchase = Buy_obj(
            total_price=product.price * item.quantity,
            reader_id=current_user.id,
            book_id=item.book_id,
            seller_id=product.seller_id or 1
        )
        db.add(new_purchase)
        db.delete(item)  # Удаляем элемент из корзины

    # Фиксируем изменения в БД один раз после успешной обработки всего цикла
    db.commit()

    # Симуляция уведомлений
    print(f"🔊 СИСТЕМА УВЕДОМЛЕНИЙ:\n"
          f"-> АДМИНУ: Совершена продажа на сумму {total_price} ₽\n"
          f"-> КЛИЕНТУ ({current_user.email}): Заказ оплачен. Списано {total_price} ₽\n"
          f"-> ПРОДАВЦАМ: Получена оплата за товары.")
          
    return {"status": "success", "redirect": "/purchase/success"}


@app.get('/purchase/success')
def cat_success(request: Request, current_user: User_obj = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name='success.html', context={'user': current_user})

# --- ЛИЧНЫЙ КАБИНЕТ ПРОДАВЦА ---

@app.get('/seller/dashboard')
async def seller_dashboard(request: Request, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user or current_user.role != 'seller':
        return RedirectResponse(url='/')
    
    query = select(Product_obj).where(Product_obj.seller_id == current_user.id)
    sell_products = db.execute(query).scalars().all()
    return templates.TemplateResponse(
        request=request, name='seller.html', context={'product': sell_products, 'user': current_user}
    )

@app.post('/seller/book/add')
async def seller_product_add(
    title: str = Form(...), author: str = Form(...),
    product_type: str = Form(...), genre: str | None = Form(None),
    price: int = Form(...), stock_quantity: int = Form(...),
    preview_text: str = Form(...), image_url: str | None = Form(None),
    current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)
):
    if not current_user or current_user.role != 'seller':
        raise HTTPException(status_code=403)
    new_product = Product_obj(
        title=title, author=author, product_type=product_type, genre=genre,
        price=price, stock_quantity=stock_quantity, preview_text=preview_text,
        image_url=image_url, seller_id=current_user.id
    )
    db.add(new_product)
    db.commit()
    
    return RedirectResponse(url="/seller/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.post('/seller/book/delete/{book_id}')
async def seller_product_delete(book_id: int, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user or current_user.role != 'seller':
        raise HTTPException(status_code=403)
    product = db.get(Product_obj, book_id)
    if product and product.seller_id == current_user.id:
        product.is_active = False  # МЯГКОЕ УДАЛЕНИЕ (Архивация)
        
    db.commit()
    
    return RedirectResponse(url="/seller/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# --- ПАНЕЛЬ АДМИНИСТРАТОРА ---

@app.get('/admin/dashboard')
async def admin_dashboard(request: Request, current_user: User_obj = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user or current_user.role != 'admin':
        return RedirectResponse(url='/')
    
    users = db.execute(select(User_obj)).scalars().all()
    products = db.execute(select(Product_obj)).scalars().all() # Админ видит всё, включая удаленные
    purchases = db.execute(select(Buy_obj)).scalars().all()
    
    return templates.TemplateResponse(
        request=request, name='admin.html',
        context={'users': users, 'products': products, 'purchase': purchases, 'user': current_user}
    )