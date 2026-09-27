# Personal Finance Advisor Bot 💰🤖

A full-stack, responsive web application designed to help individuals monitor income, track category-wise expenses, enforce budget limits, calculate savings, and receive automated financial coaching powered by an AI & smart rule-based engine.

Built for course project evaluation, local execution, GitHub hosting, and production live deployment (e.g., Render).

---

## 🌟 Key Features

1. **Interactive Financial Dashboard**
   - Real-time monthly metrics: **Monthly Income**, **Total Expenses**, **Current Savings**, **Savings Percentage**, and **Transaction Count**.
   - Dynamic **Category Breakdown Doughnut Chart** powered by Chart.js.
   - Financial Health Scoring (Grade A+ to D with progress meter).
   - Recent transactions feed with instant deletion capability.
   - Immediate **Budget Exceeded Alert Banners** when spending exceeds recommended limits.

2. **Income Management**
   - Easily set and update monthly take-home salary/income in ₹ (INR).
   - Automatically synchronizes with SQLite database.
   - Seamless month-by-month historical tracking.

3. **Expense Tracking & Filtering**
   - Record outgoing expenses with amount (₹), category, date, and description.
   - 9 standard categories:
     - 🍔 **Food**
     - 🏠 **Rent**
     - 🚌 **Transport**
     - 🎮 **Entertainment**
     - 🛍️ **Shopping**
     - 🎓 **Education**
     - 🩺 **Healthcare**
     - ⚡ **Utilities**
     - 🏷️ **Other**
   - Real-time instant search by description and dropdown filter by category.
   - One-click expense deletion with confirmation.

4. **Automatic Financial Calculations**
   - Computes Total Outflow, Net Savings (`Income - Expenses`), Savings Percentage (`Savings / Income * 100`), and Category Breakdown.
   - Standard reference course benchmark:
     - **Income:** ₹20,000
     - **Expenses:** ₹11,000
     - **Savings:** ₹9,000 (45.0% Savings Rate)

5. **Budget Advisor (Sensible 50/30/20 Benchmark)**
   - Calculates recommended budget ceilings for each category based on income:
     - **Needs (50%):** Rent (25%), Food (15%), Utilities (5%), Healthcare (5%)
     - **Wants & Growth (30%):** Transport (10%), Education (5%), Entertainment (5%), Shopping (5%), Other (5%)
     - **Target Savings (20%):** Preserved for emergency funds and wealth building.
   - Real-time progress bars: Green (<80%), Amber (80-100%), Red (>100% Exceeded).
   - Variance calculation (`Recommended - Actual`) showing remaining funds or deficit.

6. **AI Financial Advisor (Dual-Engine Architecture)**
   - **Offline Mode (Default):** Deterministic, intelligent rule-based engine that evaluates spending leaks, identifies breached categories, calculates exact savings shortfalls, and gives tailored coaching without requiring any third-party credentials.
   - **Live AI Mode:** Seamlessly connects to **Google Gemini** (`gemini-1.5-flash`) or **OpenAI** (`gpt-4o-mini`) when an API key is placed in `.env`.
   - Generates actionable, realistic guidance such as:
     - *"You spent ₹3,500 on entertainment this month, which is above your suggested limit of ₹2,000."*
     - *"You currently save ₹6,000 per month. Reducing shopping expenses by ₹1,000 could increase your monthly savings."*
     - *"Emergency buffer target: Maintain ₹33,000 (3 months of essential expenses)."*

7. **Monthly Financial Summary & Audit Statement**
   - Formatted monthly executive statement.
   - Highest spending category identification with percentage share.
   - Detailed variance table for all 9 categories.
   - One-click **Print / Save as PDF** report generator.

8. **One-Click Course Demo Seeder**
   - Includes a built-in **"Load Demo"** button in the sidebar that instantly loads the exact ₹20,000 income and ₹11,000 expense benchmark for quick mentor evaluation.

---

## 🛠️ Tech Stack

- **Backend:** Python 3.10+ with [Flask](https://flask.palletsprojects.com/)
- **Database & ORM:** [SQLite3](https://www.sqlite.org/) with [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- **Production WSGI:** [Gunicorn](https://gunicorn.org/)
- **Frontend:** Semantic HTML5, Modern Responsive CSS3 (Flexbox & CSS Grid)
- **Scripting:** Vanilla JavaScript (Fetch API, DOM manipulation)
- **Visuals & Charts:** [Chart.js](https://www.chartjs.org/) & [FontAwesome 6 Icons](https://fontawesome.com/)

---

## 📁 Project Structure

```
personal-finance-advisor/
│
├── app.py                  # Main Flask backend, DB models, calculations, & AI/rule engine
├── requirements.txt        # Production Python dependencies
├── Procfile                # WSGI entrypoint for Render / Heroku / Railway
├── render.yaml             # Render Blueprint configuration
├── README.md               # Project documentation and deployment guide
├── .gitignore              # Files excluded from git
├── .env.example            # Environment variables template
│
├── templates/
│   └── index.html          # Main responsive single-page dashboard application
│
├── static/
│   ├── style.css           # Modern CSS stylesheet with responsive media queries
│   └── script.js           # Client-side controller, chart rendering, and REST API calls
│
└── instance/
    └── finance.db          # SQLite database (auto-generated on initial launch)
```

---

## 🚀 Getting Started (Run Locally)

### Prerequisites
- Python 3.10 or higher installed on your machine (`python --version` or `py --version`).
- Git installed on your system (optional, for GitHub pushing).

### Step 1: Clone or Navigate to the Project Directory
```bash
cd personal-finance-advisor
```

### Step 2: Create and Activate a Virtual Environment (Recommended)
On Windows (PowerShell / Command Prompt):
```powershell
python -m venv venv
.\venv\Scripts\activate
# Or if using 'py' launcher:
py -m venv venv
.\venv\Scripts\activate
```

On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables (Optional)
Copy `.env.example` to create your local `.env`:
```bash
# On Windows
copy .env.example .env

# On macOS / Linux
cp .env.example .env
```

> **Note:** The application operates **100% out of the box** without any API keys using its built-in Smart Rule-Based Engine. If you wish to enable live generative AI responses, simply add your Gemini or OpenAI API key in `.env`:
> ```env
> GEMINI_API_KEY=your_gemini_api_key_here
> # OR
> OPENAI_API_KEY=your_openai_api_key_here
> ```

### Step 5: Launch the Application
```bash
python app.py
# Or with py launcher:
py app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Testing & Example Course Walkthrough

1. **Instant Demo Load:**
   - In the sidebar footer, click **"Load Demo"**.
   - Watch the dashboard immediately populate with:
     - Income: **₹20,000.00**
     - Total Expenses: **₹11,000.00**
     - Net Savings: **₹9,000.00**
     - Savings Percentage: **45.0%** (Grade A+ Super Saver)
     - Breakdown chart displaying Food, Rent, Transport, Entertainment, and Utilities.
2. **Test Adding an Expense:**
   - Go to the **Expenses** tab.
   - Enter Amount: `1500`, Category: `Shopping`, Description: `New running shoes`, Date: Today.
   - Click **Add Expense**.
   - Notice the toast confirmation and the instant balance update across all tabs.
3. **Inspect the Budget Advisor:**
   - Click **Budget Advisor** in the sidebar.
   - Observe the progress bars for all 9 categories.
   - Notice how categories that exceed limits (e.g., Entertainment) display a clear red badge and actionable alert.
4. **Interact with the AI Advisor:**
   - Click **AI Financial Advisor**.
   - Click on the quick prompt chip: *"Boost Monthly Savings"*.
   - Read the tailored diagnosis detailing exact amounts, overspent areas, and emergency fund recommendations.
5. **Review the Monthly Summary:**
   - Click **Monthly Summary** to review the complete financial balance sheet.
   - Click **Print / Save PDF** for an exportable document.

---

## 🌐 How to Deploy as a Live Demo (Render)

[Render](https://render.com) provides free hosting for Python Flask web applications. Follow these steps to deploy your live demo URL:

### 1. Initialize Git and Push to GitHub

1. Open your terminal in the `personal-finance-advisor` folder.
2. Initialize git and commit:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Personal Finance Advisor Bot"
   ```
3. Create a new repository on [GitHub](https://github.com/new) named `personal-finance-advisor`.
4. Link and push your repository:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/personal-finance-advisor.git
   git push -u origin main
   ```

### 2. Deploy on Render

1. Sign up or log in to [Render](https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository (`personal-finance-advisor`).
4. Configure the Web Service settings:
   - **Name:** `personal-finance-advisor` (or any unique name)
   - **Region:** Choose the region closest to you (e.g., Singapore / Frankfurt / Oregon)
   - **Branch:** `main`
   - **Root Directory:** Leave empty (default)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
5. *(Optional)* Under **Environment Variables**, you can add:
   - `SECRET_KEY`: any random string
   - `GEMINI_API_KEY`: *(Optional, if using live Gemini AI)*
   - `OPENAI_API_KEY`: *(Optional, if using live OpenAI)*
6. Click **Deploy Web Service**.
7. Render will build the environment and provide you with a live URL (e.g., `https://personal-finance-advisor.onrender.com`).

---

## 🛡️ Security & Input Validation

- **Sanitized Inputs:** All expense amounts, income values, dates, and descriptions are strictly validated on both client and server before database persistence.
- **Graceful Error Handling:** Handled database rollback logic to prevent transaction lockups or orphaned records.
- **Protected Credentials:** No API keys are hardcoded in the codebase. All keys are read securely from server-side environment variables.
- **Offline Resilience:** If third-party AI APIs experience network issues or quota limits, the application automatically falls back to the deterministic financial engine without crashing or interruption.

---

## 📜 License
This project is open-source and created for educational and course submission purposes.
