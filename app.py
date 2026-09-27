import os
import re
import json
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pf-advisor-course-secret-key-2026')
db_path = os.path.join(app.instance_path, 'finance.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure instance directory exists
os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)

# Standard Categories
VALID_CATEGORIES = [
    "Food",
    "Rent",
    "Transport",
    "Entertainment",
    "Shopping",
    "Education",
    "Healthcare",
    "Utilities",
    "Other"
]

# Budget allocation rules based on standard 50/30/20 guidelines
# Total budgeted expenses = 80% of income, leaving 20% target savings
CATEGORY_BUDGET_RULES = {
    "Rent": 0.25,          # 25% Needs
    "Food": 0.15,          # 15% Needs
    "Transport": 0.10,     # 10% Wants/Commute
    "Utilities": 0.05,     # 5% Needs
    "Healthcare": 0.05,    # 5% Needs
    "Education": 0.05,     # 5% Growth
    "Entertainment": 0.05, # 5% Wants
    "Shopping": 0.05,      # 5% Wants
    "Other": 0.05          # 5% Misc
}

# --- Database Models ---

class Income(db.Model):
    __tablename__ = 'income'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(7), nullable=False)  # Format: YYYY-MM
    source = db.Column(db.String(100), default='Primary Salary')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "month": self.month,
            "source": self.source,
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Expense(db.Model):
    __tablename__ = 'expense'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(10), nullable=False)  # Format: YYYY-MM-DD
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "amount": round(self.amount, 2),
            "category": self.category,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


# Automatically create tables on startup
with app.app_context():
    db.create_all()


# --- Calculation & Logic Helpers ---

def get_current_month():
    return datetime.now(timezone.utc).strftime('%Y-%m')


def get_available_months():
    """Returns a sorted list of unique YYYY-MM strings from DB."""
    income_months = [row[0] for row in db.session.query(Income.month).distinct().all() if row[0]]
    expense_dates = [row[0] for row in db.session.query(Expense.date).distinct().all() if row[0]]
    expense_months = [d[:7] for d in expense_dates if len(d) >= 7]
    all_months = sorted(list(set(income_months + expense_months + [get_current_month()])), reverse=True)
    return all_months


def calculate_finances(month=None):
    """
    Computes income, expenses, savings, breakdown, and budget comparisons.
    """
    if not month:
        month = get_current_month()

    # Get income for the specific month. If not set, check for most recent income as fallback.
    income_record = Income.query.filter_by(month=month).first()
    if not income_record:
        income_record = Income.query.order_by(Income.updated_at.desc()).first()

    income_amount = income_record.amount if income_record else 0.0

    # Get expenses for the month
    expenses = Expense.query.filter(Expense.date.like(f"{month}%")).order_by(Expense.date.desc(), Expense.id.desc()).all()

    total_expenses = sum(e.amount for e in expenses)
    savings = income_amount - total_expenses
    savings_percentage = round((savings / income_amount * 100), 1) if income_amount > 0 else 0.0

    # Category-wise spending
    category_spending = {cat: 0.0 for cat in VALID_CATEGORIES}
    for e in expenses:
        cat = e.category if e.category in category_spending else "Other"
        category_spending[cat] += e.amount

    # Category budget calculations & overspending check
    budget_comparison = []
    overspending_areas = []

    for cat in VALID_CATEGORIES:
        spent = round(category_spending[cat], 2)
        rec_ratio = CATEGORY_BUDGET_RULES.get(cat, 0.05)
        recommended = round(income_amount * rec_ratio, 2)
        difference = round(recommended - spent, 2)  # positive = savings left, negative = overspent
        is_overspent = spent > recommended if recommended > 0 else (spent > 0 and income_amount > 0)
        percent_used = round((spent / recommended * 100), 1) if recommended > 0 else (100.0 if spent > 0 else 0.0)

        status = "normal"
        if percent_used >= 100:
            status = "exceeded"
        elif percent_used >= 80:
            status = "warning"

        item = {
            "category": cat,
            "recommended": recommended,
            "recommended_percent": int(rec_ratio * 100),
            "spent": spent,
            "difference": difference,
            "overspent": is_overspent,
            "overspent_amount": round(spent - recommended, 2) if is_overspent else 0.0,
            "percent_used": percent_used,
            "status": status
        }
        budget_comparison.append(item)

        if is_overspent:
            overspending_areas.append(item)

    # Highest spending category
    highest_category = None
    highest_amount = 0.0
    for cat, amt in category_spending.items():
        if amt > highest_amount:
            highest_amount = amt
            highest_category = cat

    # Category breakdown percentage of total expenses
    category_breakdown = {}
    for cat, amt in category_spending.items():
        pct = round((amt / total_expenses * 100), 1) if total_expenses > 0 else 0.0
        category_breakdown[cat] = {
            "amount": round(amt, 2),
            "percentage": pct
        }

    # Financial health status
    if income_amount == 0:
        health_status = "No Income Configured"
        health_grade = "N/A"
        health_score = 0
    elif savings < 0:
        health_status = "Deficit Spending"
        health_grade = "D"
        health_score = max(10, int(30 + (savings / income_amount) * 30))
    elif savings_percentage >= 30:
        health_status = "Super Saver (Excellent)"
        health_grade = "A+"
        health_score = min(100, int(85 + (savings_percentage - 30)))
    elif savings_percentage >= 20:
        health_status = "Healthy Financial State"
        health_grade = "A"
        health_score = int(75 + (savings_percentage - 20))
    elif savings_percentage >= 10:
        health_status = "Moderate Savings"
        health_grade = "B"
        health_score = int(60 + (savings_percentage - 10))
    else:
        health_status = "Needs Urgent Attention"
        health_grade = "C"
        health_score = int(40 + savings_percentage)

    return {
        "month": month,
        "income": round(income_amount, 2),
        "total_expenses": round(total_expenses, 2),
        "savings": round(savings, 2),
        "savings_percentage": savings_percentage,
        "remaining_balance": round(savings, 2),
        "transaction_count": len(expenses),
        "category_spending": {k: round(v, 2) for k, v in category_spending.items()},
        "category_breakdown": category_breakdown,
        "budget_comparison": budget_comparison,
        "overspending_areas": overspending_areas,
        "highest_spending_category": highest_category,
        "highest_spending_amount": round(highest_amount, 2),
        "health_status": health_status,
        "health_grade": health_grade,
        "health_score": health_score,
        "target_savings_recommended": round(income_amount * 0.20, 2)
    }


def generate_rule_based_advice(finances, custom_prompt=""):
    """
    Intelligent, deterministic rule-based financial advisor.
    Generates tailored, realistic advice based on calculated spending patterns.
    """
    income = finances["income"]
    expenses = finances["total_expenses"]
    savings = finances["savings"]
    savings_pct = finances["savings_percentage"]
    overspending = finances["overspending_areas"]
    highest_cat = finances["highest_spending_category"]
    highest_amt = finances["highest_spending_amount"]

    advice_items = []
    action_items = []

    # Case: No income set
    if income <= 0:
        return {
            "source": "Rule-Based Financial Engine (Offline Mode)",
            "summary": "Please record your monthly income to unlock personalized financial insights.",
            "recommendations": [
                "Enter your total monthly take-home salary or income in the Income section.",
                "Once income is set, the advisor automatically crafts a 50/30/20 budget recommendation."
            ],
            "action_items": ["Set monthly income using the Income form."],
            "is_ai": False
        }

    # Overspending Insights
    if overspending:
        for area in overspending:
            cat = area["category"]
            spent = area["spent"]
            rec = area["recommended"]
            excess = area["overspent_amount"]
            pct_used = area["percent_used"]

            if cat == "Entertainment":
                advice_items.append(
                    f"You spent ₹{spent:,.2f} on Entertainment this month, which is above your suggested limit of ₹{rec:,.2f} (exceeded by ₹{excess:,.2f}, {pct_used}% of budget)."
                )
            elif cat == "Shopping":
                advice_items.append(
                    f"You spent ₹{spent:,.2f} on Shopping, exceeding your recommended limit of ₹{rec:,.2f}. Cutting back by ₹{excess:,.2f} will instantly boost your net savings."
                )
            elif cat == "Food":
                advice_items.append(
                    f"Food & Dining spending reached ₹{spent:,.2f} vs. recommended ₹{rec:,.2f}. Consider meal planning or curbing takeaway orders to stay within the ₹{rec:,.2f} cap."
                )
            else:
                advice_items.append(
                    f"Your spending in {cat} is ₹{spent:,.2f}, which exceeds your suggested budget limit of ₹{rec:,.2f} by ₹{excess:,.2f}."
                )

    # Savings Insights
    if savings < 0:
        deficit = abs(savings)
        advice_items.append(
            f"ALERT: You are running a monthly deficit of ₹{deficit:,.2f}. Your total expenses (₹{expenses:,.2f}) exceed your income (₹{income:,.2f}). Immediate expense reductions in discretionary categories like Shopping and Entertainment are advised."
        )
        action_items.append("Audit all non-essential expenses and freeze discretionary purchases until next month.")
    elif savings_pct < 20:
        shortfall = round((income * 0.20) - savings, 2)
        advice_items.append(
            f"You currently save ₹{savings:,.2f} per month ({savings_pct}%). To achieve the healthy 20% savings benchmark (₹{income * 0.20:,.2f}), aim to reduce your expenses by ₹{shortfall:,.2f} across your top discretionary categories."
        )
        if highest_cat and highest_cat in ["Shopping", "Entertainment", "Other"]:
            action_items.append(f"Trim your spending in {highest_cat} (currently ₹{highest_amt:,.2f}) by at least ₹{min(shortfall, highest_amt * 0.3):,.2f}.")
        else:
            action_items.append("Track every transaction daily to identify minor leaks in your monthly budget.")
    else:
        advice_items.append(
            f"Outstanding performance! You are saving ₹{savings:,.2f} per month ({savings_pct}% of your income), well above the standard 20% savings target (₹{income * 0.20:,.2f})."
        )
        action_items.append("Consider allocating excess savings towards high-yield savings, index funds, or emergency reserves.")

    # High Category Concentration
    if highest_cat and expenses > 0:
        cat_pct = round((highest_amt / expenses * 100), 1)
        if cat_pct >= 40:
            advice_items.append(
                f"{highest_cat} represents {cat_pct}% of your entire expense pool (₹{highest_amt:,.2f}). Consolidating or negotiating bills in this area can yield maximum financial relief."
            )

    # Emergency Fund Guidance
    rec_emergency_fund = expenses * 3
    advice_items.append(
        f"Emergency Fund Target: With current monthly expenses of ₹{expenses:,.2f}, aim to maintain an emergency buffer of ₹{rec_emergency_fund:,.2f} (3 months of essential expenses)."
    )

    # If user provided a specific question
    summary_text = "Here is your personalized financial analysis based on current spending:"
    if custom_prompt.strip():
        summary_text = f"Analysis regarding your question '{custom_prompt.strip()}':"

    return {
        "source": "Smart Rule-Based Financial Engine (Offline Mode - Add API Key to activate LLM)",
        "summary": summary_text,
        "recommendations": advice_items,
        "action_items": action_items if action_items else ["Continue monitoring your daily expenses against category budgets."],
        "is_ai": False
    }


def generate_llm_advice(finances, custom_prompt=""):
    """
    Connects to external LLM (Gemini or OpenAI) if API key is provided.
    Falls back reliably to rule-based engine if keys are missing or API fails.
    """
    gemini_key = os.environ.get('GEMINI_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')

    # Prepare context data
    financial_context = {
        "monthly_income": finances["income"],
        "total_expenses": finances["total_expenses"],
        "savings": finances["savings"],
        "savings_percentage": finances["savings_percentage"],
        "highest_spending_category": finances["highest_spending_category"],
        "highest_spending_amount": finances["highest_spending_amount"],
        "overspending_categories": [
            {
                "category": o["category"],
                "spent": o["spent"],
                "recommended": o["recommended"],
                "exceeded_by": o["overspent_amount"]
            } for o in finances["overspending_areas"]
        ],
        "category_spending": finances["category_spending"]
    }

    system_instruction = (
        "You are an empathetic, practical personal finance advisor bot. "
        "Analyze the provided monthly financial snapshot for an individual. "
        "Give actionable, realistic, encouraging recommendations. "
        "Highlight specific category overspending with exact currency figures (₹ INR). "
        "Provide 3 to 5 clear bullet points and 2 practical next steps. "
        "Do not invent facts not present in the data."
    )

    user_message = (
        f"Financial Snapshot:\n{json.dumps(financial_context, indent=2)}\n\n"
        f"User Query: {custom_prompt.strip() if custom_prompt.strip() else 'Analyze my spending and give me advice.'}"
    )

    # 1. Try Gemini API if key exists
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": f"{system_instruction}\n\n{user_message}"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 800
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Parse lines or bullets
                lines = [line.strip().lstrip('*-•#0123456789. ') for line in text.split('\n') if line.strip()]
                return {
                    "source": "Google Gemini AI (Live)",
                    "summary": f"AI Financial Analysis for {finances['month']}",
                    "raw_text": text,
                    "recommendations": [l for l in lines if len(l) > 10][:6],
                    "action_items": [
                        "Review category limits weekly.",
                        "Revisit your savings target at month-end."
                    ],
                    "is_ai": True
                }
        except Exception as e:
            # Graceful fallback on network or key error
            fallback = generate_rule_based_advice(finances, custom_prompt)
            fallback["warning"] = f"Gemini API request failed ({str(e)}). Used fallback rule-based advisor."
            return fallback

    # 2. Try OpenAI API if key exists
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.4,
                "max_tokens": 800
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                lines = [line.strip().lstrip('*-•#0123456789. ') for line in text.split('\n') if line.strip()]
                return {
                    "source": "OpenAI GPT-4o-mini (Live)",
                    "summary": f"AI Financial Analysis for {finances['month']}",
                    "raw_text": text,
                    "recommendations": [l for l in lines if len(l) > 10][:6],
                    "action_items": [
                        "Keep track of discretionary spending.",
                        "Ensure emergency savings account is funded."
                    ],
                    "is_ai": True
                }
        except Exception as e:
            fallback = generate_rule_based_advice(finances, custom_prompt)
            fallback["warning"] = f"OpenAI API request failed ({str(e)}). Used fallback rule-based advisor."
            return fallback

    # Default: Transparent rule-based fallback
    return generate_rule_based_advice(finances, custom_prompt)


# --- HTTP Routes ---

@app.route('/')
def index():
    return render_template('index.html', categories=VALID_CATEGORIES)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify({
        "categories": VALID_CATEGORIES,
        "rules": CATEGORY_BUDGET_RULES
    })


@app.route('/api/months', methods=['GET'])
def get_months():
    return jsonify({
        "months": get_available_months(),
        "current_month": get_current_month()
    })


@app.route('/api/summary', methods=['GET'])
def get_summary():
    month = request.args.get('month', get_current_month())
    data = calculate_finances(month)
    data["months_available"] = get_available_months()
    return jsonify(data)


@app.route('/api/income', methods=['GET', 'POST'])
def manage_income():
    if request.method == 'GET':
        month = request.args.get('month', get_current_month())
        record = Income.query.filter_by(month=month).first()
        if not record:
            # Fallback to latest
            record = Income.query.order_by(Income.updated_at.desc()).first()
        return jsonify({
            "income": record.to_dict() if record else None,
            "month": month
        })

    # POST - Create or update income
    payload = request.get_json() or {}
    try:
        raw_amount = payload.get('amount')
        if raw_amount is None:
            return jsonify({"error": "Income amount is required"}), 400

        amount = float(raw_amount)
        if amount < 0:
            return jsonify({"error": "Income amount cannot be negative"}), 400

        month = payload.get('month', get_current_month()).strip()
        if not re.match(r'^\d{4}-\d{2}$', month):
            return jsonify({"error": "Invalid month format. Expected YYYY-MM"}), 400

        source = payload.get('source', 'Primary Income').strip() or 'Primary Income'

        record = Income.query.filter_by(month=month).first()
        if record:
            record.amount = amount
            record.source = source
            record.updated_at = datetime.now(timezone.utc)
        else:
            record = Income(amount=amount, month=month, source=source)
            db.session.add(record)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Income of ₹{amount:,.2f} updated successfully for {month}",
            "income": record.to_dict()
        }), 200

    except ValueError:
        return jsonify({"error": "Invalid income amount. Must be a valid number"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to save income: {str(e)}"}), 500


@app.route('/api/expenses', methods=['GET', 'POST'])
def manage_expenses():
    if request.method == 'GET':
        category = request.args.get('category')
        month = request.args.get('month')
        search = request.args.get('search')
        limit = request.args.get('limit', type=int)

        query = Expense.query

        if month:
            query = query.filter(Expense.date.like(f"{month}%"))
        if category and category in VALID_CATEGORIES:
            query = query.filter_by(category=category)
        if search:
            query = query.filter(Expense.description.ilike(f"%{search}%"))

        query = query.order_by(Expense.date.desc(), Expense.id.desc())

        if limit and limit > 0:
            query = query.limit(limit)

        expenses = query.all()
        return jsonify({
            "count": len(expenses),
            "expenses": [e.to_dict() for e in expenses]
        })

    # POST - Add new expense
    payload = request.get_json() or {}
    try:
        raw_amount = payload.get('amount')
        category = payload.get('category', '').strip()
        description = payload.get('description', '').strip()
        date_str = payload.get('date', '').strip()

        # Validation
        if raw_amount is None:
            return jsonify({"error": "Expense amount is required"}), 400

        amount = float(raw_amount)
        if amount <= 0:
            return jsonify({"error": "Expense amount must be greater than 0"}), 400

        if not category or category not in VALID_CATEGORIES:
            return jsonify({
                "error": f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"
            }), 400

        if not description:
            return jsonify({"error": "Description is required"}), 400
        if len(description) > 200:
            description = description[:200]

        if not date_str:
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        elif not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD"}), 400

        new_expense = Expense(
            amount=amount,
            category=category,
            description=description,
            date=date_str
        )
        db.session.add(new_expense)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Added expense ₹{amount:,.2f} under {category}",
            "expense": new_expense.to_dict()
        }), 201

    except ValueError:
        return jsonify({"error": "Invalid amount value. Must be a valid positive number"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to record expense: {str(e)}"}), 500


@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        expense = db.session.get(Expense, expense_id)
        if not expense:
            return jsonify({"error": "Expense record not found"}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Deleted expense of ₹{expense.amount:,.2f} ({expense.description})"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete expense: {str(e)}"}), 500


@app.route('/api/budget-advisor', methods=['GET'])
def get_budget_advice():
    month = request.args.get('month', get_current_month())
    finances = calculate_finances(month)
    return jsonify({
        "month": month,
        "income": finances["income"],
        "total_expenses": finances["total_expenses"],
        "savings": finances["savings"],
        "savings_percentage": finances["savings_percentage"],
        "budget_comparison": finances["budget_comparison"],
        "overspending_areas": finances["overspending_areas"],
        "rules_explanation": "Recommended budgets use sensible 50/30/20 guidelines (Needs 50%, Wants 30%, Savings 20%)."
    })


@app.route('/api/ai-advisor', methods=['POST'])
def get_ai_advice():
    payload = request.get_json() or {}
    month = payload.get('month', get_current_month())
    user_prompt = payload.get('prompt', '')

    finances = calculate_finances(month)
    advice = generate_llm_advice(finances, custom_prompt=user_prompt)
    return jsonify(advice)


@app.route('/api/monthly-summary', methods=['GET'])
def get_monthly_summary():
    month = request.args.get('month', get_current_month())
    finances = calculate_finances(month)
    rule_advice = generate_rule_based_advice(finances)

    return jsonify({
        "month": month,
        "income": finances["income"],
        "total_expenses": finances["total_expenses"],
        "savings": finances["savings"],
        "savings_percentage": finances["savings_percentage"],
        "highest_spending_category": finances["highest_spending_category"],
        "highest_spending_amount": finances["highest_spending_amount"],
        "overspending_areas": finances["overspending_areas"],
        "health_status": finances["health_status"],
        "health_grade": finances["health_grade"],
        "health_score": finances["health_score"],
        "recommendations": rule_advice["recommendations"],
        "action_items": rule_advice["action_items"],
        "category_breakdown": finances["category_breakdown"]
    })


@app.route('/api/seed', methods=['POST'])
def seed_demo_data():
    """
    Populates standard course demo data matching prompt specs:
    Income: ₹20,000
    Expenses: ₹11,000
    Savings: ₹9,000
    """
    try:
        month = get_current_month()
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        year_month = today[:7]

        # Set income: ₹20,000
        income = Income.query.filter_by(month=year_month).first()
        if not income:
            income = Income(amount=20000.0, month=year_month, source="Monthly Salary")
            db.session.add(income)
        else:
            income.amount = 20000.0

        # Sample expenses summing exactly to ₹11,000
        # Food: ₹3,200 (over ₹3,000 cap by ₹200)
        # Rent: ₹4,500 (within ₹5,000 cap)
        # Transport: ₹1,100 (within ₹2,000 cap)
        # Entertainment: ₹1,500 (over ₹1,000 cap by ₹500)
        # Utilities: ₹700 (within ₹1,000 cap)
        # Sum = 3200 + 4500 + 1100 + 1500 + 700 = 11,000
        sample_expenses = [
            {"amount": 4500.0, "category": "Rent", "description": "Apartment monthly rent", "date": f"{year_month}-02"},
            {"amount": 1800.0, "category": "Food", "description": "Monthly grocery staples", "date": f"{year_month}-05"},
            {"amount": 1400.0, "category": "Food", "description": "Weekend cafe & dinner", "date": f"{year_month}-12"},
            {"amount": 1100.0, "category": "Transport", "description": "Metro rail monthly smartcard", "date": f"{year_month}-08"},
            {"amount": 1500.0, "category": "Entertainment", "description": "Movie passes & streaming subscriptions", "date": f"{year_month}-15"},
            {"amount": 700.0, "category": "Utilities", "description": "Electricity & broadband bill", "date": f"{year_month}-18"}
        ]

        # Only add if current month has no expenses
        existing_count = Expense.query.filter(Expense.date.like(f"{year_month}%")).count()
        if existing_count == 0:
            for item in sample_expenses:
                exp = Expense(
                    amount=item["amount"],
                    category=item["category"],
                    description=item["description"],
                    date=item["date"]
                )
                db.session.add(exp)

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Demo data loaded successfully (Income: ₹20,000 | Expenses: ₹11,000 | Savings: ₹9,000)"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to seed data: {str(e)}"}), 500


@app.route('/api/reset', methods=['POST'])
def reset_all_data():
    """Resets database data for a clean testing slate."""
    try:
        Expense.query.delete()
        Income.query.delete()
        db.session.commit()
        return jsonify({"success": True, "message": "All financial records cleared successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to reset data: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
