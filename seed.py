"""
Seed script to populate the CampusCart database with demo data.
Run this after starting the app for the first time:
    python seed.py
"""
from ssp import create_app, db
from ssp.models import Users, Catalog, Notifications
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)


def seed():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # ---- ADMIN ----
        admin = Users(
            name='Admin',
            email='admin@campuscart.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role_id=3,
            is_verified=True
        )
        db.session.add(admin)

        # ---- STUDENTS ----
        student1 = Users(
            name='Parth Jain',
            email='parth@student.com',
            password=bcrypt.generate_password_hash('student123').decode('utf-8'),
            role_id=1,
            is_verified=True,
            gender='Male',
            block_no='B-204',
            phone='9876543210',
            address='VIT Bhopal, Block B'
        )
        student2 = Users(
            name='Anusha Gupta',
            email='anusha@student.com',
            password=bcrypt.generate_password_hash('student123').decode('utf-8'),
            role_id=1,
            is_verified=True,
            gender='Female',
            block_no='A-105',
            phone='9876543211',
            address='VIT Bhopal, Block A'
        )
        db.session.add_all([student1, student2])

        # ---- SERVICE PROVIDER ----
        sp1 = Users(
            name='Campus Store',
            email='store@campuscart.com',
            password=bcrypt.generate_password_hash('store123').decode('utf-8'),
            role_id=2,
            is_verified=True,
            service_type='grocery',
            service_status='active',
            phone='9876543212'
        )
        sp2 = Users(
            name='Print Hub',
            email='print@campuscart.com',
            password=bcrypt.generate_password_hash('store123').decode('utf-8'),
            role_id=2,
            is_verified=True,
            service_type='printing',
            service_status='active',
            phone='9876543213'
        )
        db.session.add_all([sp1, sp2])
        db.session.flush()

        # ---- CATALOG: GROCERY ----
        grocery_items = [
            Catalog(item_name='Apple (500g)', price=80, stock=50, category='grocery',
                    description='Fresh red apples, 500g pack',
                    image_url='https://images.unsplash.com/photo-1567306226416-28f0efdc88ce?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Energy Drink (6-pack)', price=240, stock=30, category='grocery',
                    description='Monster Energy, pack of 6 cans',
                    image_url='https://images.unsplash.com/photo-1554765915-d5fd3a7d0c70?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Peanut Butter (300g)', price=220, stock=25, category='grocery',
                    description='Creamy peanut butter, 300g jar',
                    image_url='https://images.unsplash.com/photo-1599599810694-b5ac4dd86b3f?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Mixed Fruit Jam (300g)', price=120, stock=40, category='grocery',
                    description='Kissan Mixed Fruit Jam, 300g',
                    image_url='https://images.unsplash.com/photo-1595521624036-b7140b06b9ea?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Instant Noodles (Pack of 4)', price=56, stock=100, category='grocery',
                    description='Maggi 2-minute noodles, pack of 4',
                    image_url='https://images.unsplash.com/photo-1585521324697-53b3b3baf07d?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Milk (1 Litre)', price=60, stock=40, category='grocery',
                    description='Amul Taaza Fresh Toned Milk, 1L',
                    image_url='https://images.unsplash.com/photo-1563056169-519e2b8ef4b2?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Brown Bread', price=45, stock=30, category='grocery',
                    description='Whole wheat brown bread loaf',
                    image_url='https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Biscuits (Pack of 3)', price=90, stock=60, category='grocery',
                    description='Parle-G Gold biscuits, pack of 3',
                    image_url='https://images.unsplash.com/photo-1599599810694-b5ac4dd86b3f?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
        ]
        db.session.add_all(grocery_items)

        # ---- CATALOG: STATIONERY ----
        stationery_items = [
            Catalog(item_name='Notebook (200 pages)', price=60, stock=100, category='stationery',
                    description='Classmate single-line notebook, 200 pages',
                    image_url='https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Ball Pen (Pack of 10)', price=80, stock=80, category='stationery',
                    description='Cello Finegrip pens, blue, pack of 10',
                    image_url='https://images.unsplash.com/photo-1578375245378-875030160d0f?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Highlighter Set (5 colors)', price=150, stock=40, category='stationery',
                    description='Faber-Castell highlighter set, 5 vibrant colors',
                    image_url='https://images.unsplash.com/photo-1568572933382-74d440642117?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='A4 Sheet Bundle (100)', price=180, stock=50, category='stationery',
                    description='JK Copier A4 paper, 100 sheets',
                    image_url='https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Geometry Box', price=120, stock=30, category='stationery',
                    description='Classmate Mathematical Instruments Box',
                    image_url='https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
            Catalog(item_name='Sticky Notes (Pack of 5)', price=100, stock=60, category='stationery',
                    description='3M Post-it Notes, 5 color pads',
                    image_url='https://images.unsplash.com/photo-1590080876872-06c7b4ff2c7c?w=400&h=400&fit=crop',
                    service_professional_id=sp1.id),
        ]
        db.session.add_all(stationery_items)

        # ---- CATALOG: PRINTING ----
        printing_items = [
            Catalog(item_name='B&W Print (per page)', price=3, stock=999, category='printing',
                    description='Single-sided black & white printing on A4',
                    image_url='https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?w=400&h=400&fit=crop',
                    service_professional_id=sp2.id),
            Catalog(item_name='Color Print (per page)', price=10, stock=999, category='printing',
                    description='Single-sided color printing on A4',
                    image_url='https://images.unsplash.com/photo-1596532686361-b46a14f3e6b6?w=400&h=400&fit=crop',
                    service_professional_id=sp2.id),
            Catalog(item_name='Spiral Binding', price=40, stock=100, category='printing',
                    description='Spiral binding for documents up to 200 pages',
                    image_url='https://images.unsplash.com/photo-1606180921836-ce9cae5d2923?w=400&h=400&fit=crop',
                    service_professional_id=sp2.id),
            Catalog(item_name='Lamination (A4)', price=20, stock=200, category='printing',
                    description='A4 size lamination, both sides',
                    image_url='https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=400&fit=crop',
                    service_professional_id=sp2.id),
        ]
        db.session.add_all(printing_items)

        # Welcome notification for students
        for s in [student1, student2]:
            n = Notifications(
                user_id=s.id,
                message='Welcome to CampusCart! Browse our services and place your first order.',
                event_type='system'
            )
            db.session.add(n)

        db.session.commit()
        print('✅ Database seeded successfully!')
        print('='*50)
        print('Demo Credentials:')
        print(f'  Admin:    admin@campuscart.com / admin123')
        print(f'  Student:  parth@student.com / student123')
        print(f'  Student:  anusha@student.com / student123')
        print(f'  SP:       store@campuscart.com / store123')
        print(f'  SP:       print@campuscart.com / store123')
        print('='*50)


if __name__ == '__main__':
    seed()
