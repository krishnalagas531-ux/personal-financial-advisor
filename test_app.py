import json
import unittest
from datetime import datetime, timezone
from app import app, db, Income, Expense

class PersonalFinanceAdvisorTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_page(self):
        """Verify frontend renders successfully."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Personal Finance Advisor Bot', res.data)
        self.assertIn(b'Dashboard', res.data)
        self.assertIn(b'Budget Advisor', res.data)

    def test_income_create_and_update(self):
        """Verify adding and updating monthly income."""
        current_month = datetime.now(timezone.utc).strftime('%Y-%m')
        
        # Test creating income
        payload = {"amount": 20000.0, "month": current_month, "source": "Primary Salary"}
        res = self.client.post('/api/income', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['income']['amount'], 20000.0)

        # Test updating existing month income
        update_payload = {"amount": 25000.0, "month": current_month, "source": "Updated Salary"}
        res2 = self.client.post('/api/income', json=update_payload)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2['income']['amount'], 25000.0)

        # Test invalid negative amount
        invalid_res = self.client.post('/api/income', json={"amount": -500.0, "month": current_month})
        self.assertEqual(invalid_res.status_code, 400)

    def test_expense_crud_and_validation(self):
        """Verify adding, listing, filtering, and deleting expenses."""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        
        # Add expense
        payload = {
            "amount": 1500.0,
            "category": "Food",
            "description": "Weekly grocery supermarket",
            "date": today
        }
        res = self.client.post('/api/expenses', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        exp_id = data['expense']['id']

        # Add another expense in different category
        self.client.post('/api/expenses', json={
            "amount": 2500.0,
            "category": "Entertainment",
            "description": "Concert ticket",
            "date": today
        })

        # List all
        list_res = self.client.get('/api/expenses')
        list_data = list_res.get_json()
        self.assertEqual(list_data['count'], 2)

        # Filter by category
        filter_res = self.client.get('/api/expenses?category=Food')
        filter_data = filter_res.get_json()
        self.assertEqual(filter_data['count'], 1)
        self.assertEqual(filter_data['expenses'][0]['category'], 'Food')

        # Validation error checks
        err_res1 = self.client.post('/api/expenses', json={"amount": -10, "category": "Food", "description": "test"})
        self.assertEqual(err_res1.status_code, 400)

        err_res2 = self.client.post('/api/expenses', json={"amount": 100, "category": "InvalidCategory", "description": "test"})
        self.assertEqual(err_res2.status_code, 400)

        err_res3 = self.client.post('/api/expenses', json={"amount": 100, "category": "Food", "description": ""})
        self.assertEqual(err_res3.status_code, 400)

        # Delete expense
        del_res = self.client.delete(f'/api/expenses/{exp_id}')
        self.assertEqual(del_res.status_code, 200)

        # Verify deletion
        list_after = self.client.get('/api/expenses').get_json()
        self.assertEqual(list_after['count'], 1)

    def test_course_example_calculations(self):
        """
        Verify exact course prompt calculations:
        Income = ₹20,000
        Expenses = ₹11,000
        Savings = ₹9,000
        """
        month = datetime.now(timezone.utc).strftime('%Y-%m')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Set Income ₹20,000
        self.client.post('/api/income', json={"amount": 20000.0, "month": month})

        # Add Expenses summing to ₹11,000
        expenses = [
            {"amount": 4500.0, "category": "Rent", "description": "House Rent", "date": today},
            {"amount": 3200.0, "category": "Food", "description": "Groceries & Dine", "date": today},
            {"amount": 1100.0, "category": "Transport", "description": "Metro Pass", "date": today},
            {"amount": 1500.0, "category": "Entertainment", "description": "Outing & Movies", "date": today},
            {"amount": 700.0, "category": "Utilities", "description": "Power & Internet", "date": today}
        ]
        for exp in expenses:
            self.client.post('/api/expenses', json=exp)

        # Check Summary calculations
        summary_res = self.client.get(f'/api/summary?month={month}')
        self.assertEqual(summary_res.status_code, 200)
        data = summary_res.get_json()

        self.assertEqual(data['income'], 20000.0)
        self.assertEqual(data['total_expenses'], 11000.0)
        self.assertEqual(data['savings'], 9000.0)
        self.assertEqual(data['savings_percentage'], 45.0)
        self.assertEqual(data['transaction_count'], 5)
        self.assertEqual(data['highest_spending_category'], 'Rent')
        self.assertEqual(data['highest_spending_amount'], 4500.0)

    def test_budget_advisor_recommendations(self):
        """Verify category budget limits, overspending detection, and difference calculations."""
        month = datetime.now(timezone.utc).strftime('%Y-%m')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Income ₹20,000
        # Food cap (15%) = ₹3,000
        # Entertainment cap (5%) = ₹1,000
        self.client.post('/api/income', json={"amount": 20000.0, "month": month})

        # Spend ₹3,200 on Food (over by ₹200)
        # Spend ₹1,500 on Entertainment (over by ₹500)
        # Spend ₹4,000 on Rent (within ₹5,000 cap, ₹1,000 left)
        self.client.post('/api/expenses', json={"amount": 3200.0, "category": "Food", "description": "Food", "date": today})
        self.client.post('/api/expenses', json={"amount": 1500.0, "category": "Entertainment", "description": "Gaming", "date": today})
        self.client.post('/api/expenses', json={"amount": 4000.0, "category": "Rent", "description": "Rent", "date": today})

        res = self.client.get(f'/api/budget-advisor?month={month}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Find Food in budget comparison
        food_item = next(item for item in data['budget_comparison'] if item['category'] == 'Food')
        self.assertEqual(food_item['recommended'], 3000.0)
        self.assertEqual(food_item['spent'], 3200.0)
        self.assertEqual(food_item['difference'], -200.0)
        self.assertTrue(food_item['overspent'])

        # Find Rent in budget comparison
        rent_item = next(item for item in data['budget_comparison'] if item['category'] == 'Rent')
        self.assertEqual(rent_item['recommended'], 5000.0)
        self.assertEqual(rent_item['spent'], 4000.0)
        self.assertEqual(rent_item['difference'], 1000.0)
        self.assertFalse(rent_item['overspent'])

        # Overspending areas list should contain Food and Entertainment
        overspent_cats = [o['category'] for o in data['overspending_areas']]
        self.assertIn('Food', overspent_cats)
        self.assertIn('Entertainment', overspent_cats)
        self.assertNotIn('Rent', overspent_cats)

    def test_ai_advisor_offline_rule_fallback(self):
        """Verify AI advisor produces rich, structured recommendations using the fallback engine."""
        month = datetime.now(timezone.utc).strftime('%Y-%m')
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        self.client.post('/api/income', json={"amount": 20000.0, "month": month})
        self.client.post('/api/expenses', json={"amount": 3500.0, "category": "Entertainment", "description": "Party", "date": today})

        res = self.client.post('/api/ai-advisor', json={"month": month, "prompt": "How can I improve my finances?"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertIn('Smart Rule-Based Financial Engine', data['source'])
        self.assertIsInstance(data['recommendations'], list)
        self.assertTrue(len(data['recommendations']) > 0)
        # Should detect Entertainment overspending
        rec_text = " ".join(data['recommendations'])
        self.assertIn('Entertainment', rec_text)
        self.assertIn('₹3,500.00', rec_text)

    def test_monthly_summary_endpoint(self):
        """Verify monthly summary endpoint report generation."""
        month = datetime.now(timezone.utc).strftime('%Y-%m')
        self.client.post('/api/income', json={"amount": 20000.0, "month": month})
        self.client.post('/api/expenses', json={"amount": 5000.0, "category": "Food", "description": "Meals", "date": f"{month}-01"})

        res = self.client.get(f'/api/monthly-summary?month={month}')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['income'], 20000.0)
        self.assertEqual(data['total_expenses'], 5000.0)
        self.assertEqual(data['savings'], 15000.0)
        self.assertEqual(data['highest_spending_category'], 'Food')
        self.assertIn('health_score', data)
        self.assertIn('health_grade', data)

    def test_seed_and_reset(self):
        """Verify demo data seed and reset functionalities."""
        # Seed
        seed_res = self.client.post('/api/seed')
        self.assertEqual(seed_res.status_code, 200)
        
        # Check that expenses and income are seeded
        sum_res = self.client.get('/api/summary')
        sum_data = sum_res.get_json()
        self.assertEqual(sum_data['income'], 20000.0)
        self.assertEqual(sum_data['total_expenses'], 11000.0)
        self.assertEqual(sum_data['savings'], 9000.0)

        # Reset
        reset_res = self.client.post('/api/reset')
        self.assertEqual(reset_res.status_code, 200)
        
        # Check that data is empty
        sum_after = self.client.get('/api/summary').get_json()
        self.assertEqual(sum_after['income'], 0.0)
        self.assertEqual(sum_after['total_expenses'], 0.0)

if __name__ == '__main__':
    unittest.main()
