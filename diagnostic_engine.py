"""
Comprehensive Financial Diagnostic Engine
Analyzes data across 10 key financial categories and generates health scores
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict


class FinancialDiagnostics:
    """
    Main diagnostic engine that analyzes financial health across 10 categories:
    1. Income, 2. Expenses, 3. Debt & Liabilities, 4. Assets & Investments,
    5. Insurance, 6. Financial Goals, 7. Budgeting, 8. Credit Health,
    9. Tax Situation, 10. Financial Behavior
    """
    
    def __init__(self, transactions_df, accounts_df, user_profile=None):
        self.transactions = transactions_df.copy()
        self.accounts = accounts_df.copy()
        self.user_profile = user_profile or {}
        self.diagnostics = {}
        self.gaps = []
        self.risks = []
        self.overall_score = 0
        
    def run_full_diagnostic(self):
        """Execute complete diagnostic analysis across all categories"""
        
        # Prepare data
        self._prepare_data()
        
        # Run diagnostics for each category
        self.diagnostics['income'] = self._diagnose_income()
        self.diagnostics['expenses'] = self._diagnose_expenses()
        self.diagnostics['debt_liabilities'] = self._diagnose_debt()
        self.diagnostics['assets_investments'] = self._diagnose_assets()
        self.diagnostics['insurance'] = self._diagnose_insurance()
        self.diagnostics['financial_goals'] = self._diagnose_goals()
        self.diagnostics['budgeting'] = self._diagnose_budgeting()
        self.diagnostics['credit_health'] = self._diagnose_credit()
        self.diagnostics['tax_situation'] = self._diagnose_taxes()
        self.diagnostics['financial_behavior'] = self._diagnose_behavior()
        
        # Calculate overall health score
        self._calculate_overall_score()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        # Identify data gaps for questionnaire
        questionnaire = self._generate_questionnaire()
        
        return {
            'diagnostics': self.diagnostics,
            'overall_score': self.overall_score,
            'grade': self._get_grade(self.overall_score),
            'gaps': self.gaps,
            'risks': self.risks,
            'recommendations': recommendations,
            'questionnaire': questionnaire
        }
    
    def _prepare_data(self):
        """Prepare and enrich transaction data"""
        df = self.transactions
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])
        df['month'] = df['date'].dt.to_period('M')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['amount'])
        self.transactions = df
        
    def _diagnose_income(self):
        """Category 1: Income Analysis"""
        df = self.transactions[self.transactions['type'] == 'income']
        
        if len(df) == 0:
            self.gaps.append('No income data found - unable to assess income stability')
            return {'score': 0, 'status': 'critical', 'data_available': False}
        
        # Extract income sources
        monthly_income = df.groupby('month')['amount'].sum()
        avg_monthly_income = float(monthly_income.mean()) if len(monthly_income) > 0 else 0
        income_stability = 1 - (float(monthly_income.std()) / avg_monthly_income if avg_monthly_income > 0 else 1)
        
        # Identify income sources
        income_sources = df.groupby('description')['amount'].agg(['sum', 'count']).reset_index()
        income_sources = income_sources.sort_values('sum', ascending=False)
        
        primary_income = float(income_sources.iloc[0]['sum']) if len(income_sources) > 0 else 0
        primary_dependency = primary_income / df['amount'].sum() if df['amount'].sum() > 0 else 1
        
        # Scoring
        score = 0
        if avg_monthly_income > 3000:
            score += 30
        elif avg_monthly_income > 2000:
            score += 20
        elif avg_monthly_income > 1000:
            score += 10
        
        if income_stability > 0.8:
            score += 30
        elif income_stability > 0.6:
            score += 20
        elif income_stability > 0.4:
            score += 10
        
        if primary_dependency < 0.8:  # Diversified income is good
            score += 20
        elif primary_dependency < 0.95:
            score += 10
        
        # Income growth
        if len(monthly_income) >= 3:
            recent_avg = float(monthly_income.iloc[-3:].mean())
            older_avg = float(monthly_income.iloc[:-3].mean()) if len(monthly_income) > 3 else recent_avg
            if recent_avg > older_avg * 1.1:
                score += 20
            elif recent_avg > older_avg:
                score += 10
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': min(score, 100),
            'status': status,
            'avg_monthly_income': avg_monthly_income,
            'stability': income_stability,
            'sources': len(income_sources),
            'primary_dependency': primary_dependency,
            'data_available': True,
            'details': {
                'top_sources': income_sources.head(5).to_dict('records')
            }
        }
    
    def _diagnose_expenses(self):
        """Category 2: Expenses Analysis"""
        df = self.transactions[self.transactions['type'] == 'expense']
        
        if len(df) == 0:
            return {'score': 50, 'status': 'unknown', 'data_available': False}
        
        monthly_expenses = df.groupby('month')['amount'].sum()
        avg_monthly_expenses = float(monthly_expenses.mean())
        
        # Categorize expenses
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        
        # Essential vs discretionary (simple heuristics)
        essential_keywords = ['grocery', 'groceries', 'rent', 'mortgage', 'utilities', 'insurance', 'health', 'medical']
        essential_spending = sum([float(category_spending.get(cat, 0)) for cat in category_spending.index 
                                 if any(kw in str(cat).lower() for kw in essential_keywords)])
        total_spending = float(df['amount'].sum())
        essential_ratio = essential_spending / total_spending if total_spending > 0 else 0
        
        # Get income for comparison
        income_df = self.transactions[self.transactions['type'] == 'income']
        avg_income = float(income_df.groupby('month')['amount'].sum().mean()) if len(income_df) > 0 else 0
        
        expense_ratio = avg_monthly_expenses / avg_income if avg_income > 0 else 1
        
        # Scoring
        score = 0
        if expense_ratio < 0.5:
            score += 40
        elif expense_ratio < 0.7:
            score += 30
        elif expense_ratio < 0.9:
            score += 20
        else:
            score += 0
            self.risks.append(f'High expense ratio: {expense_ratio*100:.0f}% of income')
        
        if essential_ratio > 0.5 and essential_ratio < 0.8:
            score += 30
        elif essential_ratio >= 0.8:
            score += 20
        else:
            score += 10
        
        # Expense trend
        if len(monthly_expenses) >= 3:
            recent = float(monthly_expenses.iloc[-3:].mean())
            older = float(monthly_expenses.iloc[:-3].mean()) if len(monthly_expenses) > 3 else recent
            if recent < older * 1.1:
                score += 30
            elif recent < older * 1.2:
                score += 15
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': score,
            'status': status,
            'avg_monthly_expenses': avg_monthly_expenses,
            'expense_ratio': expense_ratio,
            'essential_ratio': essential_ratio,
            'top_categories': category_spending.head(5).to_dict(),
            'data_available': True
        }
    
    def _diagnose_debt(self):
        """Category 3: Debt & Liabilities"""
        df = self.transactions
        
        # Identify debt payments
        debt_keywords = ['loan', 'credit card', 'mortgage', 'debt', 'financing', 'installment']
        debt_payments = df[df['description'].str.contains('|'.join(debt_keywords), case=False, na=False)]
        
        if len(debt_payments) == 0:
            # Could be good (no debt) or missing data
            self.gaps.append('No debt payments detected - please confirm if you have any loans or credit cards')
            return {'score': 70, 'status': 'assumed_no_debt', 'data_available': False}
        
        monthly_debt = debt_payments.groupby('month')['amount'].sum()
        avg_monthly_debt = float(monthly_debt.mean())
        
        income_df = self.transactions[self.transactions['type'] == 'income']
        avg_income = float(income_df.groupby('month')['amount'].sum().mean()) if len(income_df) > 0 else 1
        
        debt_to_income = avg_monthly_debt / avg_income if avg_income > 0 else 0
        
        # Scoring
        score = 100
        if debt_to_income > 0.5:
            score = 20
            self.risks.append(f'Very high debt-to-income ratio: {debt_to_income*100:.0f}%')
        elif debt_to_income > 0.36:
            score = 40
            self.risks.append(f'High debt-to-income ratio: {debt_to_income*100:.0f}%')
        elif debt_to_income > 0.28:
            score = 60
        elif debt_to_income > 0.15:
            score = 80
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': score,
            'status': status,
            'avg_monthly_debt': avg_monthly_debt,
            'debt_to_income': debt_to_income,
            'debt_types': len(debt_payments['description'].unique()),
            'data_available': True
        }
    
    def _diagnose_assets(self):
        """Category 4: Assets & Investments"""
        
        # Check account balances
        total_balance = float(self.accounts['balance'].sum()) if len(self.accounts) > 0 else 0
        
        # Look for investment transactions
        investment_keywords = ['invest', 'stock', 'bond', 'etf', 'mutual fund', 'dividend', 'capital gain']
        investments = self.transactions[self.transactions['description'].str.contains('|'.join(investment_keywords), case=False, na=False)]
        
        has_investments = len(investments) > 0
        investment_rate = len(investments) / len(self.transactions) if len(self.transactions) > 0 else 0
        
        # Get monthly income for ratio calculation
        income_df = self.transactions[self.transactions['type'] == 'income']
        avg_income = float(income_df.groupby('month')['amount'].sum().mean()) if len(income_df) > 0 else 1
        
        # Calculate months of expenses covered by assets
        expense_df = self.transactions[self.transactions['type'] == 'expense']
        avg_expenses = float(expense_df.groupby('month')['amount'].sum().mean()) if len(expense_df) > 0 else 1
        emergency_fund_months = total_balance / avg_expenses if avg_expenses > 0 else 0
        
        # Scoring
        score = 0
        
        # Emergency fund scoring
        if emergency_fund_months >= 6:
            score += 40
        elif emergency_fund_months >= 3:
            score += 30
        elif emergency_fund_months >= 1:
            score += 15
        else:
            self.risks.append(f'Insufficient emergency fund: only {emergency_fund_months:.1f} months of expenses')
        
        # Investment activity
        if has_investments:
            score += 30
            if investment_rate > 0.05:
                score += 20
            elif investment_rate > 0.02:
                score += 10
        else:
            self.gaps.append('No investment activity detected - consider building an investment portfolio')
            score += 10
        
        # Asset to income ratio
        asset_to_income = total_balance / (avg_income * 12) if avg_income > 0 else 0
        if asset_to_income > 1:
            score += 10
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': score,
            'status': status,
            'total_balance': total_balance,
            'emergency_fund_months': emergency_fund_months,
            'has_investments': has_investments,
            'investment_activity': investment_rate * 100,
            'data_available': True
        }
    
    def _diagnose_insurance(self):
        """Category 5: Insurance Coverage"""
        
        insurance_keywords = ['insurance', 'premium', 'policy', 'coverage', 'insurer']
        insurance_payments = self.transactions[
            self.transactions['description'].str.contains('|'.join(insurance_keywords), case=False, na=False)
        ]
        
        if len(insurance_payments) == 0:
            self.gaps.append('No insurance payments detected - please confirm your coverage status')
            return {
                'score': 30,
                'status': 'unknown',
                'data_available': False,
                'needs_questionnaire': True
            }
        
        # Analyze insurance spending
        insurance_types = insurance_payments.groupby('description')['amount'].agg(['sum', 'count'])
        monthly_premium = float(insurance_payments.groupby('month')['amount'].sum().mean())
        
        income_df = self.transactions[self.transactions['type'] == 'income']
        avg_income = float(income_df.groupby('month')['amount'].sum().mean()) if len(income_df) > 0 else 1
        insurance_ratio = monthly_premium / avg_income if avg_income > 0 else 0
        
        # Scoring (having insurance is good, but need to verify types via questionnaire)
        score = 50  # Base score for having some insurance
        
        if len(insurance_types) >= 2:
            score += 20
        if insurance_ratio > 0.02 and insurance_ratio < 0.15:
            score += 30
        
        return {
            'score': score,
            'status': 'partial',
            'monthly_premium': monthly_premium,
            'insurance_types_detected': len(insurance_types),
            'insurance_ratio': insurance_ratio,
            'data_available': True,
            'needs_questionnaire': True
        }
    
    def _diagnose_goals(self):
        """Category 6: Financial Goals"""
        
        # Goals typically require user input
        user_goals = self.user_profile.get('goals', [])
        
        if not user_goals:
            self.gaps.append('No financial goals defined - goal setting is crucial for financial success')
            return {
                'score': 40,
                'status': 'undefined',
                'data_available': False,
                'needs_questionnaire': True
            }
        
        # Analyze progress toward goals (if data available)
        score = 60  # Base score for having goals
        
        # Check savings behavior as proxy for goal progress
        savings_df = self.transactions[self.transactions['type'] == 'income']
        expense_df = self.transactions[self.transactions['type'] == 'expense']
        
        if len(savings_df) > 0 and len(expense_df) > 0:
            monthly_savings = savings_df.groupby('month')['amount'].sum() - expense_df.groupby('month')['amount'].sum()
            avg_savings = float(monthly_savings.mean()) if len(monthly_savings) > 0 else 0
            
            if avg_savings > 0:
                score += 40
        
        return {
            'score': score,
            'status': 'defined' if user_goals else 'undefined',
            'goals_count': len(user_goals),
            'data_available': bool(user_goals),
            'needs_questionnaire': not bool(user_goals)
        }
    
    def _diagnose_budgeting(self):
        """Category 7: Budgeting & Spending Control"""
        
        income_df = self.transactions[self.transactions['type'] == 'income']
        expense_df = self.transactions[self.transactions['type'] == 'expense']
        
        if len(income_df) == 0 or len(expense_df) == 0:
            return {'score': 50, 'status': 'unknown', 'data_available': False}
        
        monthly_income = income_df.groupby('month')['amount'].sum()
        monthly_expenses = expense_df.groupby('month')['amount'].sum()
        monthly_savings = monthly_income - monthly_expenses
        
        avg_savings_rate = float(monthly_savings.mean() / monthly_income.mean() * 100) if monthly_income.mean() > 0 else 0
        
        # Consistency
        savings_consistency = 1 - (float(monthly_savings.std()) / float(monthly_savings.mean())) if monthly_savings.mean() != 0 else 0
        savings_consistency = max(0, min(1, savings_consistency))
        
        # Check if spending stays within income
        overspending_months = sum(monthly_savings < 0)
        total_months = len(monthly_savings)
        
        # Scoring
        score = 0
        
        if avg_savings_rate >= 20:
            score += 40
        elif avg_savings_rate >= 15:
            score += 30
        elif avg_savings_rate >= 10:
            score += 20
        elif avg_savings_rate > 0:
            score += 10
        else:
            self.risks.append(f'Negative savings rate: {avg_savings_rate:.1f}%')
        
        if overspending_months == 0:
            score += 30
        elif overspending_months <= total_months * 0.2:
            score += 20
        elif overspending_months <= total_months * 0.4:
            score += 10
        else:
            self.risks.append(f'Frequent overspending: {overspending_months}/{total_months} months')
        
        if savings_consistency > 0.7:
            score += 30
        elif savings_consistency > 0.5:
            score += 20
        elif savings_consistency > 0.3:
            score += 10
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': score,
            'status': status,
            'avg_savings_rate': avg_savings_rate,
            'overspending_months': int(overspending_months),
            'savings_consistency': savings_consistency,
            'data_available': True
        }
    
    def _diagnose_credit(self):
        """Category 8: Credit Health"""
        
        # Look for credit card transactions
        credit_keywords = ['credit card', 'cc payment', 'visa', 'mastercard', 'amex']
        credit_txns = self.transactions[
            self.transactions['description'].str.contains('|'.join(credit_keywords), case=False, na=False)
        ]
        
        if len(credit_txns) == 0:
            self.gaps.append('No credit card activity detected - unable to assess credit health')
            return {
                'score': 60,
                'status': 'unknown',
                'data_available': False,
                'needs_questionnaire': True
            }
        
        # Analyze payment behavior
        monthly_cc_payments = credit_txns.groupby('month')['amount'].sum()
        avg_cc_payment = float(monthly_cc_payments.mean())
        
        income_df = self.transactions[self.transactions['type'] == 'income']
        avg_income = float(income_df.groupby('month')['amount'].sum().mean()) if len(income_df) > 0 else 1
        
        cc_to_income = avg_cc_payment / avg_income if avg_income > 0 else 0
        
        # Scoring
        score = 50  # Base score
        
        if cc_to_income < 0.1:
            score += 30
        elif cc_to_income < 0.2:
            score += 20
        elif cc_to_income < 0.3:
            score += 10
        else:
            self.risks.append(f'High credit card usage: {cc_to_income*100:.0f}% of income')
        
        # Regular payments (good sign)
        if len(monthly_cc_payments) >= 3:
            score += 20
        
        return {
            'score': score,
            'status': 'fair',
            'avg_monthly_cc_payment': avg_cc_payment,
            'cc_to_income_ratio': cc_to_income,
            'data_available': True,
            'needs_questionnaire': True  # For actual credit score
        }
    
    def _diagnose_taxes(self):
        """Category 9: Tax Situation"""
        
        tax_keywords = ['tax', 'irs', 'hmrc', 'revenue', 'withholding', 'refund']
        tax_txns = self.transactions[
            self.transactions['description'].str.contains('|'.join(tax_keywords), case=False, na=False)
        ]
        
        if len(tax_txns) == 0:
            self.gaps.append('No tax-related transactions detected - please verify your tax compliance')
            return {
                'score': 60,
                'status': 'unknown',
                'data_available': False,
                'needs_questionnaire': True
            }
        
        # Analyze tax payments
        tax_payments = tax_txns[tax_txns['type'] == 'expense']
        tax_refunds = tax_txns[tax_txns['type'] == 'income']
        
        total_tax_paid = float(tax_payments['amount'].sum()) if len(tax_payments) > 0 else 0
        total_refunds = float(tax_refunds['amount'].sum()) if len(tax_refunds) > 0 else 0
        
        income_df = self.transactions[self.transactions['type'] == 'income']
        total_income = float(income_df['amount'].sum()) if len(income_df) > 0 else 1
        
        effective_tax_rate = (total_tax_paid - total_refunds) / total_income if total_income > 0 else 0
        
        # Scoring (having tax activity shows compliance)
        score = 70
        
        if len(tax_payments) > 0:
            score += 20
        if effective_tax_rate > 0 and effective_tax_rate < 0.4:
            score += 10
        
        return {
            'score': score,
            'status': 'compliant',
            'total_tax_paid': total_tax_paid,
            'total_refunds': total_refunds,
            'effective_tax_rate': effective_tax_rate * 100,
            'data_available': True
        }
    
    def _diagnose_behavior(self):
        """Category 10: Financial Behavior Patterns"""
        
        df = self.transactions
        
        # Analyze spending consistency
        expense_df = df[df['type'] == 'expense']
        monthly_expenses = expense_df.groupby('month')['amount'].sum()
        expense_volatility = float(monthly_expenses.std() / monthly_expenses.mean()) if len(monthly_expenses) > 0 and monthly_expenses.mean() > 0 else 0
        
        # Analyze savings behavior
        income_df = df[df['type'] == 'income']
        monthly_income = income_df.groupby('month')['amount'].sum()
        monthly_savings = monthly_income - monthly_expenses
        
        positive_savings_months = sum(monthly_savings > 0) if len(monthly_savings) > 0 else 0
        total_months = len(monthly_savings) if len(monthly_savings) > 0 else 1
        
        # Transaction patterns
        avg_transactions_per_month = len(df) / total_months if total_months > 0 else 0
        
        # Scoring
        score = 0
        
        # Spending discipline
        if expense_volatility < 0.2:
            score += 30
        elif expense_volatility < 0.4:
            score += 20
        elif expense_volatility < 0.6:
            score += 10
        
        # Savings discipline
        savings_discipline = positive_savings_months / total_months if total_months > 0 else 0
        if savings_discipline >= 0.9:
            score += 40
        elif savings_discipline >= 0.75:
            score += 30
        elif savings_discipline >= 0.5:
            score += 20
        elif savings_discipline > 0:
            score += 10
        
        # Transaction awareness (not too many small transactions)
        if avg_transactions_per_month < 100:
            score += 30
        elif avg_transactions_per_month < 200:
            score += 20
        elif avg_transactions_per_month < 300:
            score += 10
        
        status = 'excellent' if score >= 80 else 'good' if score >= 60 else 'fair' if score >= 40 else 'poor'
        
        return {
            'score': score,
            'status': status,
            'expense_volatility': expense_volatility,
            'savings_discipline': savings_discipline,
            'avg_transactions_per_month': int(avg_transactions_per_month),
            'data_available': True
        }
    
    def _calculate_overall_score(self):
        """Calculate weighted overall financial health score"""
        weights = {
            'income': 0.15,
            'expenses': 0.10,
            'debt_liabilities': 0.15,
            'assets_investments': 0.15,
            'insurance': 0.05,
            'financial_goals': 0.05,
            'budgeting': 0.15,
            'credit_health': 0.10,
            'tax_situation': 0.05,
            'financial_behavior': 0.05
        }
        
        total_score = 0
        for category, weight in weights.items():
            category_score = self.diagnostics.get(category, {}).get('score', 0)
            total_score += category_score * weight
        
        self.overall_score = round(total_score, 1)
    
    def _get_grade(self, score):
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 45:
            return 'D+'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on diagnostics"""
        recommendations = []
        
        for category, data in self.diagnostics.items():
            score = data.get('score', 0)
            status = data.get('status', '')
            
            if category == 'income' and score < 60:
                recommendations.append({
                    'category': 'Income',
                    'priority': 'high',
                    'action': 'Diversify income sources or seek opportunities for income growth',
                    'impact': 'Increase financial stability and growth potential'
                })
            
            if category == 'expenses' and data.get('expense_ratio', 0) > 0.9:
                recommendations.append({
                    'category': 'Expenses',
                    'priority': 'high',
                    'action': 'Reduce discretionary spending - aim for 70-80% expense-to-income ratio',
                    'impact': f'Could save €{(data.get("avg_monthly_expenses", 0) * 0.2):.2f}/month'
                })
            
            if category == 'debt_liabilities' and data.get('debt_to_income', 0) > 0.36:
                recommendations.append({
                    'category': 'Debt',
                    'priority': 'critical',
                    'action': 'Create aggressive debt paydown plan - consider debt consolidation',
                    'impact': 'Improve credit score and free up monthly cash flow'
                })
            
            if category == 'assets_investments' and data.get('emergency_fund_months', 0) < 3:
                recommendations.append({
                    'category': 'Emergency Fund',
                    'priority': 'high',
                    'action': 'Build emergency fund to cover 3-6 months of expenses',
                    'impact': 'Provide financial security against unexpected events'
                })
            
            if category == 'budgeting' and data.get('avg_savings_rate', 0) < 10:
                recommendations.append({
                    'category': 'Savings',
                    'priority': 'high',
                    'action': 'Aim to save at least 15-20% of income monthly',
                    'impact': 'Build wealth and achieve financial goals faster'
                })
        
        return recommendations
    
    def _generate_questionnaire(self):
        """Generate dynamic questionnaire based on data gaps"""
        questions = []
        
        for gap in self.gaps:
            if 'insurance' in gap.lower():
                questions.append({
                    'id': 'insurance_coverage',
                    'category': 'Insurance',
                    'question': 'What types of insurance coverage do you currently have?',
                    'type': 'multiple_choice',
                    'options': ['Health', 'Life', 'Disability', 'Home/Renters', 'Auto', 'None'],
                    'required': True
                })
            
            if 'goals' in gap.lower() or 'goal' in gap.lower():
                questions.append({
                    'id': 'financial_goals',
                    'category': 'Goals',
                    'question': 'What are your top 3 financial goals for the next 5 years?',
                    'type': 'text',
                    'required': True
                })
                questions.append({
                    'id': 'risk_tolerance',
                    'category': 'Investments',
                    'question': 'How comfortable are you with investment risk?',
                    'type': 'single_choice',
                    'options': ['Very Conservative', 'Conservative', 'Moderate', 'Aggressive', 'Very Aggressive'],
                    'required': True
                })
            
            if 'debt' in gap.lower() and 'no debt' in gap.lower():
                questions.append({
                    'id': 'debt_confirmation',
                    'category': 'Debt',
                    'question': 'Do you currently have any outstanding loans or credit card debt?',
                    'type': 'yes_no',
                    'required': True
                })
            
            if 'credit' in gap.lower():
                questions.append({
                    'id': 'credit_score',
                    'category': 'Credit',
                    'question': 'What is your approximate credit score?',
                    'type': 'single_choice',
                    'options': ['Excellent (750+)', 'Good (700-749)', 'Fair (650-699)', 'Poor (600-649)', 'Very Poor (<600)', 'Unknown'],
                    'required': False
                })
        
        # Always ask about goals and risk tolerance if not provided
        if not self.user_profile.get('goals'):
            if not any(q['id'] == 'financial_goals' for q in questions):
                questions.append({
                    'id': 'financial_goals',
                    'category': 'Goals',
                    'question': 'What are your top 3 financial goals?',
                    'type': 'text',
                    'required': True
                })
        
        return questions
