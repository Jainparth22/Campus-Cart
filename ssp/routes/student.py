from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user, logout_user
from ..models import Users, Carts, Orders, ProblemReport, OrderItems, Notifications, Catalog
from .. import db
from datetime import datetime

student = Blueprint('student', __name__)


def student_required(f):
    """Decorator to require student role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 1:
            flash('Student access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@student.route('/home')
@login_required
@student_required
def home():
    unread_count = Notifications.query.filter_by(user_id=current_user.id, is_read=False).count()
    active_orders = Orders.query.filter(
        Orders.user_id == current_user.id,
        Orders.status.in_(['Pending', 'Accepted', 'In Progress'])
    ).count()
    cart_count = Carts.query.filter_by(user_id=current_user.id, status='In Cart').count()

    stats = {
        'unread_notifications': unread_count,
        'active_orders': active_orders,
        'cart_items': cart_count
    }
    return render_template('student/home.html', stats=stats)


@student.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    if request.method == 'POST':
        current_user.gender = request.form.get('gender')
        current_user.phone = request.form.get('phone')
        current_user.block_no = request.form.get('block_no')
        current_user.address = request.form.get('address')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    incomplete = not all([current_user.gender, current_user.block_no])
    return render_template('student/profile.html', user=current_user, incomplete=incomplete)


@student.route('/grocery')
@login_required
@student_required
def grocery():
    query = request.args.get('q', '')
    sort = request.args.get('sort', '')
    
    q = Catalog.query.filter_by(category='grocery', status='active')
    if query:
        q = q.filter(Catalog.item_name.ilike(f'%{query}%'))
    
    if sort == 'price_asc':
        q = q.order_by(Catalog.price.asc())
    elif sort == 'price_desc':
        q = q.order_by(Catalog.price.desc())
        
    items = q.all()
    return render_template('student/grocery.html', items=items, query=query, sort=sort)


@student.route('/printing')
@login_required
@student_required
def printing():
    query = request.args.get('q', '')
    sort = request.args.get('sort', '')
    
    q = Catalog.query.filter_by(category='printing', status='active')
    if query:
        q = q.filter(Catalog.item_name.ilike(f'%{query}%'))
    
    if sort == 'price_asc':
        q = q.order_by(Catalog.price.asc())
    elif sort == 'price_desc':
        q = q.order_by(Catalog.price.desc())
        
    items = q.all()
    return render_template('student/printing.html', items=items, query=query, sort=sort)


@student.route('/stationary')
@login_required
@student_required
def stationary():
    query = request.args.get('q', '')
    sort = request.args.get('sort', '')
    
    q = Catalog.query.filter_by(category='stationery', status='active')
    if query:
        q = q.filter(Catalog.item_name.ilike(f'%{query}%'))
    
    if sort == 'price_asc':
        q = q.order_by(Catalog.price.asc())
    elif sort == 'price_desc':
        q = q.order_by(Catalog.price.desc())
        
    items = q.all()
    return render_template('student/stationary.html', items=items, query=query, sort=sort)


@student.route('/add_to_cart', methods=['POST'])
@login_required
@student_required
def add_to_cart():
    try:
        name = request.form.get('name')
        quantity = int(request.form.get('quantity', 1))
        price = float(request.form.get('price', 0))
        notes = request.form.get('notes', '')

        if quantity <= 0 or price <= 0:
            return 'Invalid quantity or price', 400

        cart_item = Carts(
            user_id=current_user.id,
            product_name=name,
            quantity=quantity,
            price=price,
            total_price=price * quantity,
            status='In Cart',
            notes=notes
        )
        db.session.add(cart_item)
        db.session.commit()
        return 'Success'

    except Exception as e:
        db.session.rollback()
        return f'Error: {str(e)}', 500


@student.route('/cart')
@login_required
@student_required
def cart():
    cart_items = Carts.query.filter_by(user_id=current_user.id, status='In Cart').all()
    total_amount = sum(item.total_price for item in cart_items)
    return render_template('student/cart.html', cart_items=cart_items, total_amount=total_amount)


@student.route('/update_cart/<int:cart_id>', methods=['POST'])
@login_required
@student_required
def update_cart(cart_id):
    item = Carts.query.get_or_404(cart_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('student.cart'))

    new_quantity = int(request.form.get('quantity', 1))
    if new_quantity <= 0:
        db.session.delete(item)
        flash('Item removed from cart.', 'success')
    else:
        item.quantity = new_quantity
        item.calculate_total_price()
        flash('Cart updated.', 'success')
    db.session.commit()
    return redirect(url_for('student.cart'))


@student.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
@student_required
def remove_from_cart(cart_id):
    item = Carts.query.get_or_404(cart_id)
    if item.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('student.cart'))

    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'success')
    return redirect(url_for('student.cart'))


@student.route('/confirm_order', methods=['POST'])
@login_required
@student_required
def confirm_order():
    try:
        import os
        from werkzeug.utils import secure_filename

        cart_items = Carts.query.filter_by(user_id=current_user.id, status='In Cart').all()
        if not cart_items:
            flash('Your cart is empty.', 'info')
            return redirect(url_for('student.cart'))

        # Check if any cart item is a printing service
        product_names = [item.product_name for item in cart_items]
        has_printing = Catalog.query.filter(
            Catalog.item_name.in_(product_names),
            Catalog.category == 'printing'
        ).first() is not None

        # Validate: printing orders MUST have a file
        uploaded_file = request.files.get('print_file')
        has_file = uploaded_file and uploaded_file.filename != ''

        if has_printing and not has_file:
            flash('A document file is required for printing orders. Please attach your file.', 'danger')
            return redirect(url_for('student.cart'))

        total_amount = sum(item.total_price for item in cart_items) + 30  # Delivery fee
        payment_mode = request.form.get('payment_mode', 'COD')

        # Wallet Check
        if payment_mode == 'Wallet':
            if current_user.wallet_balance < total_amount:
                flash('Insufficient wallet balance!', 'danger')
                return redirect(url_for('student.cart'))
            current_user.wallet_balance -= total_amount

        # File Upload Handling (for Printing)
        file_path = None
        if has_file:
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            save_name = f"{timestamp}_{filename}"
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            uploaded_file.save(os.path.join(upload_folder, save_name))
            file_path = save_name

        new_order = Orders(
            user_id=current_user.id,
            total_price=total_amount,
            status='Pending',
            payment_mode=payment_mode,
            file_path=file_path,
            order_date=datetime.utcnow()
        )
        db.session.add(new_order)
        db.session.flush()

        for cart_item in cart_items:
            order_item = OrderItems(
                order_id=new_order.id,
                product_name=cart_item.product_name,
                quantity=cart_item.quantity,
                price=cart_item.price,
                total_price=cart_item.total_price
            )
            db.session.add(order_item)
            db.session.delete(cart_item)  # Clear cart

        notification = Notifications(
            user_id=current_user.id,
            message=f"Order #{new_order.id} placed! Mode: {payment_mode}. Total: \u20b9{total_amount}",
            status='Pending',
            event_type='order_update',
            created_date=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('student.orders'))

    except Exception as e:
        db.session.rollback()
        print(f"Order Error: {e}")
        flash(f'Error placing order: {str(e)}', 'danger')
        return redirect(url_for('student.cart'))


@student.route('/rate_order/<int:order_id>', methods=['POST'])
@login_required
@student_required
def rate_order(order_id):
    order = Orders.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return 'Unauthorized', 403
        
    if order.status != 'Completed':
        flash('You can only rate completed orders.', 'warning')
        return redirect(url_for('student.orders'))
        
    rating = request.form.get('rating')
    review = request.form.get('review')
    
    if rating:
        order.rating = int(rating)
        order.review = review
        db.session.commit()
        flash('Thank you for your feedback!', 'success')
        
    return redirect(url_for('student.orders'))


@student.route('/orders')
@login_required
@student_required
def orders():
    active_orders = Orders.query.filter(
        Orders.user_id == current_user.id,
        Orders.status.in_(['Pending', 'Accepted', 'In Progress'])
    ).order_by(Orders.order_date.desc()).all()

    past_orders = Orders.query.filter(
        Orders.user_id == current_user.id,
        Orders.status.in_(['Completed', 'Cancelled', 'Rejected'])
    ).order_by(Orders.order_date.desc()).all()

    return render_template('student/orders.html', orders=active_orders, past_orders=past_orders)


@student.route('/cancel_order/<int:order_id>', methods=['POST'])
@login_required
@student_required
def cancel_order(order_id):
    order = Orders.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('student.orders'))

    if order.status != 'Pending':
        flash('Only pending orders can be cancelled.', 'danger')
        return redirect(url_for('student.orders'))

    order.status = 'Cancelled'
    notification = Notifications(
        user_id=current_user.id,
        message=f"Order #{order.id} has been cancelled.",
        status='Cancelled',
        event_type='order_update',
        created_date=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()

    flash('Order cancelled successfully.', 'success')
    return redirect(url_for('student.orders'))


@student.route('/notifications')
@login_required
@student_required
def notifications():
    notifs = Notifications.query.filter_by(user_id=current_user.id).order_by(Notifications.created_date.desc()).all()
    return render_template('student/notifications.html', notifications=notifs)


@student.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
@login_required
@student_required
def mark_notification_read(notification_id):
    notification = Notifications.query.get(notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return '', 204


@student.route('/report_prblm', methods=['GET', 'POST'])
@login_required
@student_required
def report_prblm():
    if request.method == 'POST':
        description = request.form.get('description')
        if description:
            report = ProblemReport(description=description, user_id=current_user.id)
            db.session.add(report)
            db.session.commit()
            flash('Your problem has been reported successfully.', 'success')
        return redirect(url_for('student.report_prblm'))

    reports = ProblemReport.query.filter_by(user_id=current_user.id).order_by(ProblemReport.date_reported.desc()).all()
    return render_template('report_prblm.html', reports=reports)


@student.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))