from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from ..models import Users, Orders, ProblemReport, OrderItems, Notifications, Catalog
from .. import db
from datetime import datetime
from sqlalchemy import func

ssp = Blueprint('ssp', __name__)


def ssp_required(f):
    """Decorator to require service provider role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 2:
            flash('Service Provider access required.', 'danger')
            return redirect(url_for('auth.login'))
        if not current_user.is_verified:
            flash('Your account is pending admin verification.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def _get_my_catalog_names():
    """Return list of item names belonging to the current SSP's catalog."""
    items = Catalog.query.filter_by(
        service_professional_id=current_user.id,
        status='active'
    ).all()
    return [item.item_name for item in items]


def _get_orders_for_me(statuses):
    """
    Return orders that contain at least one item matching this vendor's catalog
    AND are in the given statuses. If the vendor has no catalog items yet,
    fall back to showing all orders with those statuses (graceful degradation).
    """
    my_names = _get_my_catalog_names()
    q = Orders.query.filter(Orders.status.in_(statuses))

    if my_names:
        q = q.join(OrderItems, OrderItems.order_id == Orders.id).filter(
            OrderItems.product_name.in_(my_names)
        ).distinct()

    return q.order_by(Orders.order_date.desc()).all()


@ssp.route('/dashboard')
@login_required
@ssp_required
def ssp_index():
    my_names = _get_my_catalog_names()

    if my_names:
        base_q = Orders.query.join(OrderItems, OrderItems.order_id == Orders.id).filter(
            OrderItems.product_name.in_(my_names)
        ).distinct()
        pending_count = base_q.filter(Orders.status == 'Pending').count()
        active_count = base_q.filter(Orders.status.in_(['Accepted', 'In Progress'])).count()
        completed_count = base_q.filter(Orders.status == 'Completed').count()
    else:
        pending_count = active_count = completed_count = 0

    catalog_count = Catalog.query.filter_by(
        service_professional_id=current_user.id, status='active'
    ).count()

    # Per-vendor revenue and cancelled
    my_completed = Orders.query.filter(
        Orders.ssp_id == current_user.id,
        Orders.status == 'Completed'
    )
    total_revenue = db.session.query(func.sum(Orders.total_price)).filter(
        Orders.ssp_id == current_user.id,
        Orders.status == 'Completed'
    ).scalar() or 0

    stats = {
        'pending': pending_count,
        'active': active_count,
        'completed': completed_count,
        'catalog': catalog_count,
        'total_revenue': round(total_revenue, 2),
    }
    return render_template('service_professional/home.html', stats=stats)


@ssp.route('/order_requests')
@login_required
@ssp_required
def order_requests():
    pending_orders = _get_orders_for_me(['Pending'])
    return render_template('service_professional/order-request.html', orders=pending_orders)


@ssp.route('/update_order_status/<int:order_id>', methods=['POST'])
@login_required
@ssp_required
def update_order_status(order_id):
    order = Orders.query.get_or_404(order_id)
    status = request.form.get('status')
    eta = request.form.get('eta')

    if status == 'Accepted':
        order.status = 'Accepted'
        order.eta = eta
        order.ssp_id = current_user.id
        message = f"Your order #{order.id} has been accepted! ETA: {eta}."
    elif status == 'Rejected':
        order.status = 'Rejected'
        order.ssp_id = current_user.id
        order.eta = None
        message = f"Sorry, your order #{order.id} was rejected."
    else:
        flash('Invalid status.', 'danger')
        return redirect(url_for('ssp.order_requests'))

    notification = Notifications(
        user_id=order.user_id,
        message=message,
        status=status,
        eta=eta if status == 'Accepted' else None,
        event_type='order_update',
        created_date=datetime.utcnow(),
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()

    flash(f"Order #{order.id} has been {status.lower()}.", 'success')
    return redirect(url_for('ssp.order_requests'))


@ssp.route('/active_orders')
@login_required
@ssp_required
def active_orders():
    # Show orders that were accepted by THIS vendor (ssp_id set) or
    # orders still pending that belong to this vendor's catalog
    active = Orders.query.filter(
        Orders.ssp_id == current_user.id,
        Orders.status.in_(['Accepted', 'In Progress', 'Pending'])
    ).order_by(Orders.order_date.desc()).all()

    # Also include pending orders matching this vendor's catalog that have no ssp yet
    unassigned = _get_orders_for_me(['Pending'])
    seen_ids = {o.id for o in active}
    for o in unassigned:
        if o.id not in seen_ids:
            active.append(o)

    return render_template('service_professional/active-orders.html', orders=active)


@ssp.route('/complete_order/<int:order_id>', methods=['POST'])
@login_required
@ssp_required
def complete_order(order_id):
    order = Orders.query.get_or_404(order_id)

    # Only the assigned vendor can complete the order
    if order.ssp_id and order.ssp_id != current_user.id:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    order.status = 'Completed'
    if not order.ssp_id:
        order.ssp_id = current_user.id

    notification = Notifications(
        user_id=order.user_id,
        message=f"Your order #{order.id} has been completed! Thank you for using CampusCart.",
        status='Completed',
        event_type='order_update',
        created_date=datetime.utcnow(),
        is_read=False
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Order marked as completed'})


@ssp.route('/profile', methods=['GET', 'POST'])
@login_required
@ssp_required
def profile():
    if request.method == 'POST':
        current_user.gender = request.form.get('gender')
        current_user.service_type = request.form.get('service_type')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('ssp.profile'))

    return render_template('service_professional/profile.html', user=current_user)


@ssp.route('/edit_catalog', methods=['GET', 'POST'])
@login_required
@ssp_required
def edit_catalog():
    # Only show THIS vendor's catalog items
    catalog_items = Catalog.query.filter_by(
        service_professional_id=current_user.id,
        status='active'
    ).all()

    if request.method == 'POST':
        try:
            item_names = request.form.getlist('item_name[]')
            prices = request.form.getlist('item_price[]')
            stocks = request.form.getlist('stock[]')
            categories = request.form.getlist('category[]')
            descriptions = request.form.getlist('description[]')
            image_urls = request.form.getlist('image_url[]')

            for i in range(len(item_names)):
                if item_names[i].strip():
                    catalog_item = Catalog(
                        service_professional_id=current_user.id,
                        item_name=item_names[i],
                        price=float(prices[i]),
                        stock=int(stocks[i]),
                        category=categories[i],
                        description=descriptions[i] if i < len(descriptions) else '',
                        image_url=image_urls[i] if i < len(image_urls) else ''
                    )
                    db.session.add(catalog_item)

            db.session.commit()
            flash('Catalog updated successfully!', 'success')
            return redirect(url_for('ssp.edit_catalog'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating catalog: {str(e)}', 'danger')
            return redirect(url_for('ssp.edit_catalog'))

    return render_template('service_professional/edit-catalog.html', catalog_items=catalog_items)


@ssp.route('/delete_catalog_item/<int:catalog_id>', methods=['POST'])
@login_required
@ssp_required
def delete_catalog_item(catalog_id):
    try:
        item = Catalog.query.get_or_404(catalog_id)
        # Only allow vendor to delete their own items
        if item.service_professional_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permission denied'})
        item.status = 'deleted'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Item deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@ssp.route('/report', methods=['GET', 'POST'])
@login_required
@ssp_required
def report():
    if request.method == 'POST':
        description = request.form.get('description')
        if description:
            report = ProblemReport(description=description, user_id=current_user.id)
            db.session.add(report)
            db.session.commit()
            flash('Your problem has been reported successfully.', 'success')
        return redirect(url_for('ssp.report'))

    reports = ProblemReport.query.filter_by(user_id=current_user.id).order_by(ProblemReport.date_reported.desc()).all()
    return render_template('service_professional/report.html', reports=reports)


@ssp.route('/notifications')
@login_required
@ssp_required
def notifications():
    notifs = Notifications.query.filter_by(user_id=current_user.id).order_by(Notifications.created_date.desc()).all()
    return render_template('service_professional/notifications.html', notifications=notifs)


@ssp.route('/feedback')
@login_required
@ssp_required
def feedback():
    # Per-vendor stats
    total_orders = Orders.query.filter_by(ssp_id=current_user.id, status='Completed').count()
    total_revenue = db.session.query(func.sum(Orders.total_price)).filter(
        Orders.ssp_id == current_user.id, Orders.status == 'Completed'
    ).scalar() or 0
    pending_orders = Orders.query.filter_by(ssp_id=current_user.id, status='Pending').count()
    cancelled_orders = Orders.query.filter_by(ssp_id=current_user.id, status='Cancelled').count()

    # Ratings for this vendor's completed orders
    rated_orders = Orders.query.filter(
        Orders.ssp_id == current_user.id,
        Orders.rating.isnot(None)
    ).all()
    avg_rating = round(
        sum(o.rating for o in rated_orders) / len(rated_orders), 1
    ) if rated_orders else None

    stats = {
        'total_orders': total_orders,
        'total_revenue': round(total_revenue, 2),
        'pending_orders': pending_orders,
        'cancelled_orders': cancelled_orders,
        'avg_rating': avg_rating,
        'total_rated': len(rated_orders),
    }
    return render_template('service_professional/feedback.html', stats=stats)