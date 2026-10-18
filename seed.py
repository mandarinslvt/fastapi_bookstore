from database import SessionLocal
from models import Product_obj, User_obj, Promo_obj
from datetime import datetime, timedelta

def seed_users_and_promo():
    db = SessionLocal()
    try:
        reader1 = User_obj(
            username='client1',
            password='123',
            role='client',
            name='Alexandr',
            second_name='Novikov',
            age=22,
            email='novikov32@example.com',
            phone='+7-888-222-00-00',
            balance=9000000,
        )

        reader2 = User_obj(
            username='client2',
            password='123',
            role='client',
            name='Andrey',
            second_name='Aliev',
            age=20,
            email='andrey22@example.com',
            phone='+7-887-332-10-10',
            balance=100040,
        )

        seller = User_obj(
            username='seller1',
            password='124',
            role='seller',
            company_name='Издательство Page',
            email='page@example.com',
            balance=0
        )

        admin = User_obj(
            username='admin1',
            password='admin',
            role='admin',
            name='Главный',
            second_name='Администратор',
            email='admin@example.com',
            balance=0
        )

        promo = Promo_obj(
            code="SALE100", 
            discount_amount=100, 
            active=True, 
            expires_at=datetime.now() + timedelta(days=10)
        )

        db.add_all([reader1, reader2, seller, admin, promo])
        db.commit()
        
        seller_id = seller.id
        print('Ready: Клиенты, Продавец, Админ и Промокоды успешно созданы.')
        return seller_id
        
    except Exception as e:
        print(f'ERROR в создании пользователей: {e}')
        db.rollback()
        return None
    finally:
        db.close()

def seed_products(seller_id):
    if not seller_id:
        print("Пропуск создания товаров: отсутствует ID продавца.")
        return

    db = SessionLocal()
    try:
        book1 = Product_obj(
            title='Мартин Иден',
            author='Джек Лондон',
            year=1909,
            genre='Проза',
            price=430,
            image_url='images/martin-iden.jpg',
            product_type='книга',
            stock_quantity=15,
            preview_text='Мартин Иден — знаменитый роман Джека Лондона о человеке из низов, который благодаря железной воле и упорному труду выучился и стал знаменитым писателем...',
            seller_id=seller_id
        )
        book2 = Product_obj(
            title="Преступление и наказание", 
            author='Фёдор Достоевский', 
            year=1866,
            genre='Роман', 
            price=425,
            image_url='images/prestuplenie-and-nakazanie.jpg',
            product_type='книга',
            stock_quantity=8,
            preview_text='В начале июля, в чрезвычайно жаркое время, под вечер, один молодой человек вышел из своей каморки, которую нанимал от жильцов в С — м переулке, на улицу...',
            seller_id=seller_id
        )
        book3 = Product_obj(
            title='Кафка на пляже',
            author='Харуки Мураками',
            year=2002,
            genre='Проза',
            price=720,
            image_url='images/kafka-na-plyazhe.jpg',
            product_type='книга',
            stock_quantity=0, # Проверим статус "Нет в наличии"
            preview_text='Всякий раз, когда я собираюсь бежать из дому, идет дождь. Точнее сказать, не просто дождь — во всем этом чувствуется какая-то закономерность...',
            seller_id=seller_id
        )
        book4 = Product_obj(
            title='Белые ночи',
            author='Фёдор Достоевский',
            year=1848,
            genre='Повесть',
            price=300,
            image_url='images/white-nights.jpg',
            product_type='книга',
            stock_quantity=12,
            preview_text='Была чудная ночь, такая ночь, которая разве только и может быть тогда, когда мы молоды, любезный читатель. Небо было такое звездное, такое светлое небо...',
            seller_id=seller_id
        )

        # Аксессуары и письменные принадлежности
        accessory1 = Product_obj(
            title='Кожаная закладка "Дракон"',
            author='Мастерская Ли',
            price=250,
            image_url='images/bookmark-dragon.jpg',
            product_type='закладки',
            stock_quantity=50,
            preview_text='Удобная винтажная закладка ручной работы из натуральной кожи для истинных любителей чтения.',
            seller_id=seller_id
        )
        stationery1 = Product_obj(
            title='Перьевая ручка',
            author='Parker Pen Co.',
            price=1500,
            image_url='images/parker-pen.jpg',
            product_type='письменные принадлежности',
            stock_quantity=5,
            preview_text='Классическая перьевая ручка черного цвета с позолоченной отделкой. Идеально для ведения читательского дневника.',
            seller_id=seller_id
        )

        db.add_all([book1, book2, book3, book4, accessory1, stationery1])
        db.commit()
        print('Ready: Ассортимент товаров (Все 4 книги, Закладки, Ручки) успешно добавлен.')

    except Exception as e:
        print(f'ERROR в создании товаров: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    # Порядок важен: сначала пользователи (чтобы получить seller_id), затем их товары
    created_seller_id = seed_users_and_promo()
    seed_products(created_seller_id)
    print('Already.')