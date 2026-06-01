# Research Journal SaaS

A comprehensive multi-tenant academic publishing platform built with Flask.

## 🚀 Features

### Core Features
- **Multi-tenant Architecture** - Multiple journals on single platform
- **Article Management** - Submit, review, and publish research articles
- **Peer Review System** - Assign reviewers and manage review workflow
- **User Roles** - Super Admin, Admin, Editor, Reviewer, Author, Subscriber

### Advanced Features
- **AI-Powered Tools**
  - Content creation assistant
  - Grammar checking
  - Abstract generation
  - Citation formatting
  
- **Billing & Subscriptions**
  - Multiple subscription plans (Free, Basic, Pro, Enterprise)
  - Razorpay payment integration
  - Offline payment support
  - Transaction management

- **Custom Domains**
  - Journal-specific custom domains
  - SSL auto-provisioning
  - DNS configuration support

- **Analytics Dashboard**
  - User growth tracking
  - Submission trends
  - Revenue analytics
  - Platform health monitoring

- **Communication**
  - Email notifications
  - In-app notification system
  - Video conferencing rooms
  - Team collaboration

## 🛠️ Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite (Development) / PostgreSQL (Production)
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Authentication:** Flask-Login
- **Forms:** Flask-WTF
- **Email:** Flask-Mail
- **Payments:** Razorpay
- **AI:** Google Gemini API

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Khushi-verma816/RESEARCH_JOURNAL_SAAS.git
cd RESEARCH_JOURNAL_SAAS
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
flask db upgrade
```

6. **Run the application**
```bash
python run.py
```

Visit: `http://localhost:3000`

## 🔧 Configuration

Create a `.env` file with:

```env
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///researchforge.db
FLASK_ENV=development
FLASK_DEBUG=1

# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret

# AI API
GEMINI_API_KEY=your-gemini-api-key
```

## 📁 Project Structure

```
research/
├── app/
│   ├── core/              # Core utilities
│   ├── models/            # Database models
│   ├── modules/           # Application modules
│   │   ├── admin/         # Admin panel
│   │   ├── articles/      # Article management
│   │   ├── auth/          # Authentication
│   │   ├── billing/       # Billing & subscriptions
│   │   ├── ai/            # AI features
│   │   └── ...
│   ├── static/            # CSS, JS, images
│   ├── templates/         # HTML templates
│   └── utils/             # Helper functions
├── migrations/            # Database migrations
├── config.py             # Configuration
├── run.py               # Application entry point
└── requirements.txt     # Dependencies
```

## 👥 User Roles

- **Super Admin** - Full platform control
- **Admin** - Journal management
- **Tenant Owner** - Journal owner with billing access
- **Editor** - Review and publish articles
- **Reviewer** - Review assigned articles
- **Author** - Submit articles
- **Subscriber** - Read-only access

## 🔐 Security Features

- CSRF protection
- Password hashing (Werkzeug)
- Secure session management
- Email verification
- Password reset functionality
- Role-based access control

## 📊 Database Models

- User
- Tenant (Journal)
- Article
- Subscription
- Transaction
- Notification
- Testimonial
- Custom Domain Request

## 🚀 Deployment

### Production Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Use PostgreSQL database
- [ ] Configure proper SECRET_KEY
- [ ] Set up email service
- [ ] Configure payment gateway
- [ ] Enable SSL/HTTPS
- [ ] Set up backup system
- [ ] Configure monitoring

## 📝 License

This project is proprietary software.

## 👨‍💻 Author

**Khushi Verma**
- GitHub: [@Khushi-verma816](https://github.com/Khushi-verma816)

## 🤝 Contributing

This is a private project. For inquiries, please contact the author.

## 📧 Support

For support, email: khushiverma7804@gmail.com

---

**Built with ❤️ using Flask**
