# CampusCart — Campus Service Management Platform

CampusCart is a web-based platform designed to automate and streamline essential campus services — groceries, stationery, and printing — for students at **VIT Bhopal University**. Built with a clean role-based architecture, it connects Students, Service Providers, and Admins on a single platform. This project was developed by **Group 49** during the **2024–25 Interim Semester**.

---

## 🌟 Features

### For Students
- Browse **Grocery**, **Stationery**, and **Printing** service catalogs
- Add items to cart with quantity controls
- Place orders with **COD** or **Campus Wallet** payment
- Upload documents for **printing orders** (required, validated server-side)
- Real-time **order progress tracking** (Pending → Accepted → In Progress → Completed)
- **Cancel** pending orders
- **Rate** completed orders with an interactive ⭐ star widget and optional review
- **Forgot Password** self-service reset flow (no email required)
- Notifications center with unread badge counts

### For Service Providers (SSP)
- View **only their own** order requests (vendor-scoped, multi-vendor compatible)
- **Download attached print files** directly from order request cards
- Accept orders with ETA or reject with one click
- Mark active orders as Completed
- Manage their own **catalog** (add, edit, delete items per category)
- Per-vendor **statistics dashboard**: revenue, completed/pending/cancelled orders, average star rating
- Report problems to admin

### For Admins
- Full platform oversight: users, orders, catalog, revenue
- Verify or reject pending Service Provider registrations
- Resolve problem reports with replies (notifies user automatically)
- Send broadcast or targeted notifications to any user(s)

---

## 🏗 Project Structure

```
CampusCart/
├── ssp/
│   ├── __init__.py          # App factory — creates Flask app, DB, uploads dir
│   ├── auth.py              # Auth blueprint: login, register, forgot/reset password
│   ├── models.py            # SQLAlchemy models: Users, Orders, OrderItems, Catalog, etc.
│   ├── views.py
│   ├── routes/
│   │   ├── student.py       # Student blueprint
│   │   ├── ssp.py           # Service Provider blueprint (vendor-scoped)
│   │   └── admin.py         # Admin blueprint
│   ├── static/
│   │   └── uploads/         # Uploaded print files (auto-created on startup)
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── register.html
│       ├── forgot_password.html
│       ├── resetpass.html
│       ├── student/
│       ├── service_professional/
│       └── admin/
├── instance/
│   └── database.db          # SQLite DB (auto-created)
├── Data Seeding Scripts/
├── run.py                   # Entry point
├── seed.py                  # Database seed script
├── requirements.txt
├── Procfile                 # Render/Heroku deployment
└── render.yaml              # Render deployment config
```

---

## 🚀 Routes Reference

### Authentication (`/`)
| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/` | Login |
| GET/POST | `/register` | Register (student or service provider) |
| GET | `/logout` | Logout |
| GET/POST | `/forgot-password` | Step 1: Enter registered email |
| GET/POST | `/reset-password` | Step 2: Set new password |

### Student (`/student/`)
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/student/home` | Student dashboard |
| GET | `/student/grocery` | Browse grocery catalog |
| GET | `/student/stationary` | Browse stationery catalog |
| GET | `/student/printing` | Browse printing services |
| POST | `/student/add_to_cart` | Add item to cart |
| GET | `/student/cart` | View cart |
| POST | `/student/confirm_order` | Place order (with optional file upload) |
| POST | `/student/cancel_order/<id>` | Cancel pending order |
| POST | `/student/rate_order/<id>` | Rate completed order |
| GET | `/student/orders` | View active & past orders |
| GET | `/student/notifications` | Notifications |
| GET/POST | `/student/profile` | View/edit profile |
| GET/POST | `/student/report_prblm` | Report a problem |

### Service Provider (`/ssp/`)
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/ssp/dashboard` | Vendor dashboard (per-vendor stats) |
| GET | `/ssp/order_requests` | View pending orders for this vendor |
| POST | `/ssp/update_order_status/<id>` | Accept or reject an order |
| GET | `/ssp/active_orders` | View active orders |
| POST | `/ssp/complete_order/<id>` | Mark order as completed |
| GET/POST | `/ssp/edit_catalog` | Manage this vendor's catalog |
| POST | `/ssp/delete_catalog_item/<id>` | Soft-delete a catalog item |
| GET | `/ssp/feedback` | View per-vendor stats & ratings |
| GET | `/ssp/notifications` | Notifications |
| GET/POST | `/ssp/profile` | View/edit profile |
| GET/POST | `/ssp/report` | Report a problem |

### Admin (`/admin/`)
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/admin/dashboard` | Admin dashboard |
| GET | `/admin/verify-users` | Pending SP verifications |
| POST | `/admin/approve_user/<id>` | Approve a service provider |
| POST | `/admin/reject_user/<id>` | Reject & delete a service provider |
| GET | `/admin/orders` | All orders |
| GET | `/admin/users` | All users |
| GET | `/admin/catalog` | Full platform catalog |
| GET | `/admin/resolve-problems` | Open problem reports |
| POST | `/admin/reply_report/<id>` | Reply & resolve a report |
| GET | `/admin/send_notification` | Notification composer |
| POST | `/admin/add_notification` | Send notification |

---

## 🗄 Database Models

| Model | Key Fields |
|-------|------------|
| `Users` | `id`, `email`, `name`, `password`, `role_id` (1=Student, 2=SSP, 3=Admin), `is_verified`, `wallet_balance`, `service_type` |
| `Orders` | `id`, `user_id`, `ssp_id`, `status`, `total_price`, `payment_mode`, `file_path`, `rating`, `review` |
| `OrderItems` | `id`, `order_id`, `product_name`, `quantity`, `price`, `total_price` |
| `Catalog` | `id`, `service_professional_id`, `item_name`, `price`, `stock`, `category`, `status` |
| `Carts` | `id`, `user_id`, `product_name`, `quantity`, `price`, `status` |
| `Notifications` | `id`, `user_id`, `message`, `is_read`, `event_type` |
| `ProblemReport` | `id`, `user_id`, `description`, `admin_reply`, `status` |

---

## 🛠 Setup & Installation

### Prerequisites
- Python 3.8+
- pip

### Steps

```bash
# 1. Clone the repository
git clone <repository_url>
cd CampusCart

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Seed demo data (optional but recommended)
# This creates demo users, vendors, and catalog items
python seed.py

# 5. Run the application
python run.py
```

The app will be available at **`http://127.0.0.1:8080/`**

> 💡 **Note:** The SQLite database and `static/uploads/` directory are created automatically on the first run. 
> The default admin user is also automatically created:
> - **Admin:** `admin@campuscart.com` / `admin123`

### Seed Demo Data (Highly Recommended)

To test the application fully, you should populate the database with demo users (Students, Service Providers) and catalog items. Open a new terminal (with the virtual environment activated) and run:

```bash
python seed.py
```

This script generates mock data and the following demo credentials:

| Role | Email | Password |
|------|-------|----------|
| Student | parth@student.com | student123 |
| Service Provider | store@campuscart.com | store123 |
| Admin | admin@campuscart.com | admin123 |

---

## ☁️ Deployment (Render)

The app is configured for deployment on [Render](https://render.com) via `render.yaml` and `Procfile`:

```
web: gunicorn run:app
```

**Important:** The `static/uploads/` directory is created automatically inside `create_app()` so it exists even under Gunicorn (no `__main__` block required).

---

## 🔒 Security

- **Password hashing** via `flask-bcrypt`
- **Role-based access control (RBAC)** — each blueprint has a decorator (`student_required`, `ssp_required`, `admin_required`)
- **Multi-vendor isolation** — SSPs can only view/manage their own orders and catalog items
- **File upload validation** — only orders with printing items require a file; uploads use `secure_filename` with a timestamp prefix
- **Session management** via `flask-login`

---



## 🔮 Future Enhancements

- Mobile application (Flutter/React Native)
- Email/SMS notifications for order updates
- AI-based service recommendations
- Payment gateway integration (Razorpay/UPI)
- Dynamic pricing and discount coupons

---

## 👥 Contributors

| Name | ID |
|------|----|
| Anusha Gupta | 23BCE10866 |
| Arnav Shukla | 23BCE10173 |
| Parth Jain | 23BCE10156 |
| Sabiha Khan | 23BCE11638 |
| Viya Sharma | 23BCE11351 |

---

## 📝 License

This project is licensed under the **MIT License**.

---

## 🙏 Acknowledgements

Special thanks to **Dr. Jay Prakash Maurya** and the faculty of VIT Bhopal University for their guidance and support throughout the development of this project.