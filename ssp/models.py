from . import db
from flask_login import UserMixin
from datetime import datetime


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role_id = db.Column(db.Integer, nullable=False)  # 1=Student, 2=Service Provider, 3=Admin
    created_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Profile fields
    gender = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    block_no = db.Column(db.String(50), nullable=True)

    # Service provider specific
    service_type = db.Column(db.String(50), nullable=True)  # grocery, stationery, printing
    service_status = db.Column(db.String(20), default='active')
    is_verified = db.Column(db.Boolean, default=False)  # Admin must verify service providers
    
    # Wallet (New)
    wallet_balance = db.Column(db.Float, default=5000.0)

    # Relationships
    notifications = db.relationship('Notifications', backref='user', lazy=True)
    orders = db.relationship('Orders', backref='user', lazy=True, foreign_keys='Orders.user_id')
    carts = db.relationship('Carts', backref='user', lazy=True)
    catalog_items = db.relationship('Catalog', backref='service_professional', lazy=True, cascade='all, delete-orphan')
    reports = db.relationship('ProblemReport', backref='user', lazy=True)

    def __repr__(self):
        return f'<Users {self.name}, Role {self.role_id}>'

    def get_id(self):
        return str(self.id)

    @property
    def role_name(self):
        roles = {1: 'Student', 2: 'Service Provider', 3: 'Admin'}
        return roles.get(self.role_id, 'Unknown')


class ProblemReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    admin_reply = db.Column(db.Text, default='No replies yet')
    status = db.Column(db.String(20), default='open')  # open, resolved
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Report {self.id}>'


class Carts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Float, nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='In Cart')  # In Cart, Ordered
    notes = db.Column(db.Text, nullable=True)

    def calculate_total_price(self):
        self.total_price = self.price * self.quantity


class Notifications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=True)
    eta = db.Column(db.String(50), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    event_type = db.Column(db.String(50))  # order_update, admin_message, system

    def __repr__(self):
        return f"<Notification {self.message}>"


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Pending, Accepted, In Progress, Completed, Cancelled, Rejected
    eta = db.Column(db.String(50), nullable=True)
    ssp_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # New Fields
    payment_mode = db.Column(db.String(20), default='COD')  # 'Wallet' or 'COD'
    file_path = db.Column(db.String(255), nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)

    items = db.relationship('OrderItems', backref='order', lazy=True)
    service_provider = db.relationship('Users', foreign_keys=[ssp_id], backref='assigned_orders')

    def __repr__(self):
        return f'<Order {self.id}>'


class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def calculate_total_price(self):
        self.total_price = self.price * self.quantity


class Catalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_professional_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    item_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(50), nullable=False)  # grocery, stationery, printing
    image_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, deleted

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'image_url': self.image_url
        }

    def __repr__(self):
        return f'<Catalog Item {self.item_name}>'