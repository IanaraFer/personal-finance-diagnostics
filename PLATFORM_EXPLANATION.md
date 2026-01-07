# Personal Finance Diagnostics Platform - How It Works

## Overview

The Personal Finance Diagnostics platform is a web-based financial analysis tool that helps users understand their spending habits, assess financial health, and receive actionable recommendations. The platform combines an interactive web application with a standalone offline analyzer, offering flexibility for both connected and offline usage.

---

## Platform Architecture

### 1. **Web Application (Flask Backend)**

The main platform runs on **Flask**, a lightweight Python web framework, and serves three core functions:

#### **User Authentication & Access Control**
- Users register with email and password
- Credentials are securely hashed and stored in SQLite database
- Login required for all main features (except demo)
- Paid access model: users must purchase €1.99 beta access to unlock full functionality

#### **File Upload & Processing**
- Users upload transaction data in multiple formats:
  - **CSV** (comma-separated values)
  - **Excel** (.xlsx, .xls)
  - **JSON** (array of transaction objects)
- Files are parsed and validated
- Data normalized for consistent analysis

#### **Financial Analysis Engine**
- Automatically processes uploaded transactions
- Calculates key metrics:
  - Total income and expenses
  - Savings rate
  - Budget distribution by category
  - Financial health score (0-100)
- Generates alerts for overspending or budget risks
- Produces personalized recommendations

#### **Payment Processing (Stripe Integration)**
- Stripe Checkout handles €1.99 payment
- Payment status tracked in user database
- Webhook confirms purchase and marks user as paid
- Access automatically granted upon successful payment

---

## User Journey

### Step 1: Registration & Authentication
```
User visits website
         ↓
Register with email + password (optional: buy access link to Stripe)
         ↓
Credentials stored in SQLite
         ↓
Login with email + password
```

### Step 2: Payment (Beta Access)
```
Unpaid users redirected to paywall (/pay)
         ↓
Click "Buy Access (€1.99)" → Stripe Checkout
         ↓
Complete payment with credit card
         ↓
Stripe webhook confirms transaction
         ↓
User marked as "paid" in database
         ↓
Access to full platform granted
```

### Step 3: Upload & Analysis
```
Click "Upload Transaction Data"
         ↓
Select CSV, Excel, or JSON file
         ↓
File uploaded to server (/upload endpoint)
         ↓
Parser detects format automatically
         ↓
Data normalized (columns lowercased, types validated)
         ↓
Financial analysis engine processes data
         ↓
Results displayed with:
  - Financial Health Score
  - Income/Expense breakdown
  - Savings rate
  - Alerts & recommendations
```

### Step 4: View Results & Dashboard
```
Interactive dashboard displays:
         ↓
  - Health score card with grade (A/B/C/D)
  - Key metrics (total income, expenses, savings rate)
  - Visual charts (Plotly)
  - Category breakdown
  - Alerts (warnings for overspending)
  - Recommendations (actionable advice)
```

---

## Standalone Demo Tool

### What is demo.html?

**demo.html** is a completely **offline, client-side financial analyzer** that requires:
- No server connection
- No login or payment
- Runs entirely in the browser

### How It Works

1. **Download demo.html** (available without payment)
2. **Open in web browser** locally (File → Open demo.html)
3. **Upload transaction file** (CSV, Excel, or JSON)
4. **Get instant analysis** (same metrics as web version, calculated in browser)
5. **No data stored** (completely private, runs locally)

### Supported Formats in Demo

| Format | Extension | Example |
|--------|-----------|---------|
| CSV | .csv | date,amount,type,category,description |
| Excel | .xlsx, .xls | Standard spreadsheet with columns |
| JSON | .json | Array of transaction objects |

---

## Data Processing Pipeline

### 1. **File Parsing**

```
User uploads file
         ↓
Detect file type (by extension)
         ↓
Parse content:
  - CSV: Split by commas, parse rows
  - Excel: Extract first sheet, convert to JSON
  - JSON: Parse JSON structure directly
         ↓
Normalize column names (lowercase)
         ↓
Validate required fields: date, amount, type, category
```

### 2. **Financial Analysis**

The platform calculates:

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Total Income** | Sum of all "income" type transactions | Monthly/period earnings |
| **Total Expenses** | Sum of all "expense" type transactions | Monthly/period spending |
| **Savings Rate** | (Income - Expenses) / Income × 100 | % of income saved |
| **Health Score** | 0-100 weighted calculation | Overall financial health |

### 3. **Score Calculation**

The health score (0-100) factors in:
- **Savings Rate** (40 points): >20% = 40 pts, >10% = 30 pts, >0% = 20 pts
- **Spending vs Income** (30 points): Expenses < Income = 30 pts
- **Income Level** (20 points): >€2000 = 20 pts, >€1000 = 10 pts
- **Category Diversity** (10 points): >5 categories = 10 pts

**Grades Assigned:**
- **A (80+)**: Excellent - Strong financial habits
- **B (60-79)**: Good - Healthy financial practices
- **C (40-59)**: Fair - Room for improvement
- **D (<40)**: Needs Improvement - Action required

### 4. **Alert Generation**

Alerts are triggered when:
- ⚠️ **Spending ≥ Income**: "Spending meets or exceeds income. Review budget urgently."
- ⚠️ **Savings Rate < 10%**: "Savings rate below 10%. Aim to raise gradually."

### 5. **Recommendations**

Personalized advice based on:
- **Low savings rate**: "Increase savings by €X/month to reach 15% rate"
- **High category spending**: If one category >30% of expenses: "Consider reducing X spending"

---

## Technology Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | Flask (Python) | Web server, routing, API endpoints |
| Database | SQLite | User credentials, payment status |
| Analytics | Pandas, NumPy | Data processing, calculations |
| Charts | Plotly | Interactive visualizations |
| Payment | Stripe API | Payment processing & webhooks |
| Auth | Flask-Login | Session management |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI | HTML + CSS | User interface, forms |
| Charts | Plotly.js | Interactive visualizations |
| Client-side parsing | XLSX.js library | Excel parsing in browser |
| Demo analyzer | Vanilla JavaScript | Offline calculation engine |

### Deployment
| Platform | Service | Purpose |
|----------|---------|---------|
| Render | Web hosting | Live application hosting |
| SQLite | Database file | Local data persistence |
| Stripe | Payment gateway | Payment processing |

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid INTEGER DEFAULT 0  -- 0 = unpaid, 1 = paid
);
```

### Key Fields
- **email**: User login identifier
- **password**: Hashed with werkzeug.security
- **paid**: Boolean flag (1 = beta access granted, 0 = payment required)

---

## API Endpoints

### Authentication Routes
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/register` | GET, POST | User registration form + processing |
| `/login` | GET, POST | Login form + authentication |
| `/logout` | GET | Clear session, redirect to login |

### Main Application Routes
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard (requires login + paid) |
| `/upload` | GET, POST | File upload form + processing |
| `/api/analyze` | POST | JSON API for analysis data |
| `/download` | GET | Export results as CSV/JSON |

### Payment Routes
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/checkout` | POST | Initiate Stripe Checkout session |
| `/success` | GET | Redirect after successful payment |
| `/cancel` | GET | Redirect if payment cancelled |
| `/stripe/webhook` | POST | Webhook for payment confirmation |

### Health & Admin
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service status check |

---

## Payment Flow (Stripe Integration)

```
User clicks "Buy Access"
         ↓
POST /checkout (sends user email + price ID)
         ↓
Stripe API creates Checkout session
         ↓
User redirected to Stripe payment page
         ↓
User enters card details
         ↓
Payment processed
         ↓
Stripe sends webhook notification to /stripe/webhook
         ↓
App extracts email from webhook data
         ↓
App calls user_store.mark_paid(email)
         ↓
User database updated (paid = 1)
         ↓
User redirected to /success page
         ↓
Next login → full access granted
```

---

## Key Features Explained

### 1. **Multi-Format File Support**
- **Why**: Users have data in different formats (Excel, CSV from banks, custom JSON)
- **How**: Auto-detection by file extension + format-specific parser
- **Benefit**: No need for users to convert files manually

### 2. **Offline Demo Mode**
- **Why**: Enable testing without server; protect privacy; no setup needed
- **How**: Standalone HTML + JavaScript (uses XLSX.js library for Excel parsing)
- **Benefit**: Testers can validate functionality immediately; zero deployment friction

### 3. **Paid Beta Access**
- **Why**: Monetize while gathering feedback; control user base
- **How**: €1.99 Stripe payment with webhook validation
- **Benefit**: Revenue stream + sustainable user testing community

### 4. **Automated Alerts & Recommendations**
- **Why**: Actionable insights, not just metrics
- **How**: Rule-based engine evaluates against thresholds (savings rate, category percentages)
- **Benefit**: Users get personalized guidance immediately

### 5. **Health Score Grading**
- **Why**: Simple, easy-to-understand summary of financial health
- **How**: Weighted point system (0-100 range) with letter grades
- **Benefit**: Users quickly understand overall financial position

---

## Security Features

### Authentication
- ✅ Password hashing (werkzeug.security)
- ✅ Session-based auth (Flask-Login)
- ✅ Login required for sensitive routes

### Data Protection
- ✅ User uploads stored in isolated `/data/uploads` folder
- ✅ Database (SQLite) local file with restricted access
- ✅ HTTPS enforced in production (Render)

### Payment Security
- ✅ Stripe PCI-compliant payment processing
- ✅ Webhook signature verification (STRIPE_WEBHOOK_SECRET)
- ✅ No card data stored locally

### Environment Configuration
- ✅ Sensitive keys stored in environment variables
- ✅ Support for Azure Key Vault (if configured)
- ✅ Fallback to local secrets for development

---

## File Format Examples

### CSV Format
```csv
date,amount,type,category,description
2024-01-01,2500,income,salary,Monthly salary
2024-01-05,150,expense,groceries,Weekly shopping
2024-01-10,80,expense,utilities,Electricity bill
2024-01-15,200,expense,entertainment,Movies and dining
```

### Excel Format
Same columns as CSV, organized in spreadsheet:
| date | amount | type | category | description |
|------|--------|------|----------|-------------|
| 2024-01-01 | 2500 | income | salary | Monthly salary |
| 2024-01-05 | 150 | expense | groceries | Weekly shopping |

### JSON Format
```json
[
  {
    "date": "2024-01-01",
    "amount": 2500,
    "type": "income",
    "category": "salary",
    "description": "Monthly salary"
  },
  {
    "date": "2024-01-05",
    "amount": 150,
    "type": "expense",
    "category": "groceries",
    "description": "Weekly shopping"
  }
]
```

---

## Deployment Overview

### Local Development
```powershell
# Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run
$env:APP_SECRET_KEY="dev-secret"
python app.py

# Access
Open http://localhost:5000
```

### Production (Render)
```
- Repository: Push to GitHub
- Render detects Procfile
- Builds with Python 3.11 (runtime.txt)
- Installs dependencies (requirements.txt)
- Starts gunicorn server on PORT=$PORT
- Live at: https://your-app.onrender.com
```

---

## Monitoring & Support

### Health Check
```bash
GET /health
Response: {"status": "OK"}
```

Used by Render to monitor application availability.

### Logs
- **Local**: Console output during development
- **Production**: Render dashboard + tail logs in CLI

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "File format not supported" | Check extension (.csv, .xlsx, .xls, .json) |
| Payment webhook not firing | Verify STRIPE_WEBHOOK_SECRET set correctly |
| Data not loading | Check CSV/Excel column names (case-insensitive) |
| Demo.html won't parse Excel | Ensure XLSX library CDN is accessible |

---

## Summary: User Value Proposition

1. **Quick Insights**: Upload data → get financial health score in seconds
2. **Actionable Advice**: Personalized alerts and recommendations based on data
3. **Flexible Input**: Multiple file formats supported (CSV, Excel, JSON)
4. **Privacy**: Offline demo available; uploaded data isolated
5. **Affordability**: €1.99 beta access to full platform
6. **Ease of Use**: No complex setup; web-based or offline options

---

## Next Steps for Users

1. **Register** for free account
2. **Download demo.html** or **buy beta access** (€1.99)
3. **Upload financial data** in any supported format
4. **Review health score** and personalized recommendations
5. **Take action** on alerts and suggestions

---

**Last Updated**: January 2026
**Platform Status**: Active (Render) + Demo (Offline)
