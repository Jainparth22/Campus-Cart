from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from ..models import Users, Notifications, Orders, OrderItems, ProblemReport, Catalog
from .. import db
from datetime import datetime
from sqlalchemy import func

admin = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role_id != 3:
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin.route('/dashboard')
@login_required
@admin_required
def home():
    # Dashboard statistics
    total_students = Users.query.filter_by(role_id=1).count()
    total_sps = Users.query.filter_by(role_id=2).count()
    pending_verifications = Users.query.filter_by(role_id=2, is_verified=False).count()
    total_orders = Orders.query.count()
    pending_orders = Orders.query.filter_by(status='Pending').count()
    completed_orders = Orders.query.filter_by(status='Completed').count()
    total_revenue = db.session.query(func.sum(Orders.total_price)).filter(Orders.status == 'Completed').scalar() or 0
    open_reports = ProblemReport.query.filter_by(status='open').count()
    total_catalog = Catalog.query.filter_by(status='active').count()

    stats = {
        'total_students': total_students,
        'total_sps': total_sps,
        'pending_verifications': pending_verifications,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': round(total_revenue, 2),
        'open_reports': open_reports,
        'total_catalog': total_catalog
    }
    return render_template('admin/home.html', stats=stats)


@admin.route('/verify-users')
@login_required
@admin_required
def verify_users():
    unverified = Users.query.filter_by(role_id=2, is_verified=False).all()
    verified = Users.query.filter_by(role_id=2, is_verified=True).all()
    return render_template('admin/verify-users.html', unverified=unverified, verified=verified)


@admin.route('/approve_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_user(user_id):
    user = Users.query.get_or_404(user_id)
    user.is_verified = True
    notification = Notifications(
        user_id=user.id,
        message='Your account has been verified by the admin. You can now log in and start providing services.',
        event_type='system',
        created_date=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()
    flash(f'{user.name} has been verified successfully.', 'success')
    return redirect(url_for('admin.verify_users'))


@admin.route('/reject_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_user(user_id):
    user = Users.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'{user.name} has been rejected and removed.', 'success')
    return redirect(url_for('admin.verify_users'))


@admin.route('/resolve-problems')
@login_required
@admin_required
def resolve_problems():
    open_reports = ProblemReport.query.filter_by(status='open').order_by(ProblemReport.date_reported.desc()).all()
    resolved_reports = ProblemReport.query.filter_by(status='resolved').order_by(ProblemReport.date_reported.desc()).all()
    return render_template('admin/resolve-problem.html', open_reports=open_reports, resolved_reports=resolved_reports)


@admin.route('/reply_report/<int:report_id>', methods=['POST'])
@login_required
@admin_required
def reply_report(report_id):
    report = ProblemReport.query.get_or_404(report_id)
    reply = request.form.get('reply')
    if reply:
        report.admin_reply = reply
        report.status = 'resolved'
        notification = Notifications(
            user_id=report.user_id,
            message=f'Your problem report #{report.id} has been resolved. Admin reply: {reply}',
            event_type='admin_message',
            created_date=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        flash('Reply sent and report marked as resolved.', 'success')
    return redirect(url_for('admin.resolve_problems'))


@admin.route('/orders')
@login_required
@admin_required
def all_orders():
    orders = Orders.query.order_by(Orders.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@admin.route('/users')
@login_required
@admin_required
def all_users():
    students = Users.query.filter_by(role_id=1).all()
    service_providers = Users.query.filter_by(role_id=2).all()
    return render_template('admin/users.html', students=students, service_providers=service_providers)


@admin.route('/catalog')
@login_required
@admin_required
def manage_catalog():
    items = Catalog.query.filter_by(status='active').all()
    return render_template('admin/catalog.html', items=items)


@admin.route('/add_notification', methods=['POST'])
@login_required
@admin_required
def add_notification():
    user_id = request.form.get('user_id')
    message = request.form.get('message')

    if user_id == 'all':
        users = Users.query.all()
        for u in users:
            n = Notifications(user_id=u.id, message=message, event_type='admin_message', created_date=datetime.utcnow())
            db.session.add(n)
    else:
        n = Notifications(user_id=int(user_id), message=message, event_type='admin_message', created_date=datetime.utcnow())
        db.session.add(n)

    db.session.commit()
    flash('Notification sent successfully.', 'success')
    return redirect(url_for('admin.home'))


@admin.route('/send_notification')
@login_required
@admin_required
def send_notification():
    users = Users.query.all()
    return render_template('admin/send-notification.html', users=users)
