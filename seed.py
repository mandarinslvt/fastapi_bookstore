from database import SessionLocal
from models import Book_obj, Reader_obj, Promo_obj
from datetime import datetime, timedelta

def db_data():
    db = SessionLocal()

    try:
        book1 = Book_obj(
            title = 'Мартин Иден',
            author = 'Джек Лондон',
            year = 1909,
            genre = 'Проза',
            price = 430,
            image_url = 'images/martin-iden.jpg',
            # isbn = ,
        )
        book2 = Book_obj(
            title = "Преступление и наказание", 
            author = 'Фёдор Достоевский', 
            year = 1866,
            genre = 'Роман', 
            price = 425,
            image_url = 'images/prestuplenie-and-nakazanie.jpg',
        )
        book3 = Book_obj(
            title = 'Кафка на пляже',
            author = 'Харуки Мураками',
            year = 2002,
            genre = 'Проза',
            price = 720,
            image_url = 'images/kafka-na-plyazhe.jpg',
        )
        book4 = Book_obj(
            title = 'Белые ночи',
            author = 'Фёдор Достоевский',
            year = 1848,
            genre = 'Повесть',
            price = 300,
            image_url = 'images/white-nights.jpg'
            # isbn = ,
        )

        db.add_all([book1, book2, book3, book4])

        db.commit()
        print('Ready "db_data".')

    except Exception as e:
        print(f'ERROR: {e}')
        db.rollback()
    finally:
        db.close()

def promocodes():
    db = SessionLocal()
    try:
        promo = Promo_obj(
            code="SALE100", 
            discount_amount=100, 
            active=True, 
            expires_at=datetime.now() + timedelta(days=10)
        )
        db.add(promo)
        db.commit()
        print('Ready "promocodes".')
    except Exception as e:
        print(f'ERROR в промокодах: {e}')
        db.rollback()
    finally:
        db.close()
    
def seed_reader():
    db = SessionLocal()
    try:
        reader1 = Reader_obj(
            name = 'Alexandr',
            second_name = 'Novikov',
            age = 22,
            email = 'novikov32@example.com',
            phone = "+7-888-222-00-00",
            balance = 9000000,
            # registration_date
        )
        reader2 = Reader_obj(
            name = 'Andrey',
            second_name = 'Aliev',
            age = 20,
            email = 'andrey22@example.com',
            phone = '+7-887-332-10-10',
            balance = 100040,
        )

        db.add_all([reader1, reader2])
        
        db.commit()
        print('Ready "seed_readers".')
        
    except Exception as e:
        print(f'ERROR: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    db_data()
    seed_reader()
    promocodes()