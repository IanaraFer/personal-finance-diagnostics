#!/usr/bin/env python3
"""
Complete Financial Account Analysis and Diagnostic Report Generator
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# Load data
tx = pd.read_csv('data/transactions_from_pdf.csv')
acct = pd.read_csv('data/accounts_from_pdf.csv')

# Parse dates
tx['date'] = pd.to_datetime(tx['date'], format='mixed', dayfirst=True, errors='coerce')
tx = tx.dropna(subset=['date'])

# Convert amounts
tx['amount'] = pd.to_numeric(tx['amount'], errors='coerce')
tx = tx.dropna(subset=['amount'])

# Separate income and expenses
income_tx = tx[tx['type'].str.lower() == 'income']
expense_tx = tx[tx['type'].str.lower() == 'expense']

# ============================================================================
# SECTION 1: BASIC STATISTICS
# ============================================================================
total_income = income_tx['amount'].sum()
total_expenses = expense_tx['amount'].sum()
net_balance = total_income - total_expenses
num_transactions = len(tx)
date_min = tx['date'].min()
date_max = tx['date'].max()
days_span = (date_max - date_min).days
months_span = days_span / 30.44

print("=" * 80)
print("COMPLETE FINANCIAL ACCOUNT DIAGNOSTIC REPORT")
print("=" * 80)
print()

print("1. BASIC ACCOUNT INFORMATION")
print("-" * 80)
print(f"Account Name: Revolut EUR Account (Checking)")
print(f"Analysis Period: {date_min.strftime('%d %b %Y')} to {date_max.strftime('%d %b %Y')}")
print(f"Duration: {days_span} days (~{months_span:.1f} months)")
print(f"Total Transactions Analyzed: {num_transactions:,}")
print(f"Current Balance: EUR 0.00")
print()

# ============================================================================
# SECTION 2: INCOME ANALYSIS
# ============================================================================
print("2. INCOME ANALYSIS")
print("-" * 80)
print(f"Total Income: EUR {total_income:,.2f}")
print(f"Income Transactions: {len(income_tx):,}")
print(f"Average Transaction: EUR {income_tx['amount'].mean():.2f}")
print(f"Largest Transaction: EUR {income_tx['amount'].max():.2f}")
print(f"Smallest Transaction: EUR {income_tx['amount'].min():.2f}")

income_by_cat = income_tx.groupby('category')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
print("\nIncome Sources:")
for cat, row in income_by_cat.iterrows():
    pct = (row['sum'] / total_income) * 100
    print(f"  {cat}: EUR {row['sum']:,.2f} ({pct:.1f}%) - {int(row['count'])} transactions")

# Monthly income trend
tx['month'] = tx['date'].dt.strftime('%Y-%m')
income_tx['month'] = income_tx['date'].dt.strftime('%Y-%m')
expense_tx['month'] = expense_tx['date'].dt.strftime('%Y-%m')
monthly_income = income_tx.groupby('month')['amount'].sum()
print(f"\nAverage Monthly Income: EUR {monthly_income.mean():.2f}")
print(f"Monthly Income Range: EUR {monthly_income.min():.2f} to EUR {monthly_income.max():.2f}")
print()

# ============================================================================
# SECTION 3: EXPENSE ANALYSIS
# ============================================================================
print("3. EXPENSE ANALYSIS")
print("-" * 80)
print(f"Total Expenses: EUR {total_expenses:,.2f}")
print(f"Expense Transactions: {len(expense_tx):,}")
print(f"Average Transaction: EUR {expense_tx['amount'].mean():.2f}")
print(f"Largest Transaction: EUR {expense_tx['amount'].max():.2f}")
print(f"Smallest Transaction: EUR {expense_tx['amount'].min():.2f}")

expense_by_cat = expense_tx.groupby('category')['amount'].agg(['sum', 'count']).sort_values('sum', ascending=False)
print("\nExpense Breakdown by Category:")
for cat, row in expense_by_cat.iterrows():
    pct = (row['sum'] / total_expenses) * 100
    print(f"  {cat}: EUR {row['sum']:,.2f} ({pct:.1f}%) - {int(row['count'])} transactions")

# Monthly expense trend
monthly_expense = expense_tx.groupby('month')['amount'].sum()
print(f"\nAverage Monthly Expenses: EUR {monthly_expense.mean():.2f}")
print(f"Monthly Expense Range: EUR {monthly_expense.min():.2f} to EUR {monthly_expense.max():.2f}")
print()

# ============================================================================
# SECTION 4: SAVINGS & PROFITABILITY METRICS
# ============================================================================
print("4. SAVINGS & PROFITABILITY METRICS")
print("-" * 80)
if total_income > 0:
    savings_rate = (net_balance / total_income) * 100
else:
    savings_rate = 0

print(f"Total Net Balance: EUR {net_balance:,.2f}")
print(f"Savings Rate: {savings_rate:.1f}%")
print(f"Expense Ratio: {((total_expenses/total_income)*100 if total_income > 0 else 0):.1f}%")

# Monthly savings breakdown
print("\nMonthly Savings Trend:")
monthly_summary = []
for month in sorted(tx['month'].unique()):
    month_inc = income_tx[income_tx['month'] == month]['amount'].sum()
    month_exp = expense_tx[expense_tx['month'] == month]['amount'].sum()
    month_net = month_inc - month_exp
    month_save_rate = (month_net / month_inc * 100) if month_inc > 0 else 0
    monthly_summary.append({'month': month, 'income': month_inc, 'expense': month_exp, 'net': month_net, 'save_rate': month_save_rate})
    print(f"  {month}: Income EUR {month_inc:,.2f} | Expenses EUR {month_exp:,.2f} | Net EUR {month_net:,.2f} | Savings Rate {month_save_rate:.1f}%")

# Emergency fund assessment
avg_monthly_expense = monthly_expense.mean()
emergency_fund_months = 3
target_emergency_fund = avg_monthly_expense * emergency_fund_months
print(f"\nEmergency Fund Analysis:")
print(f"  Average Monthly Expenses: EUR {avg_monthly_expense:.2f}")
print(f"  Recommended Emergency Fund (3 months): EUR {target_emergency_fund:.2f}")
print(f"  Current Liquid Savings: EUR 0.00")
print(f"  Emergency Fund Status: INSUFFICIENT (0% of target)")
print()

# ============================================================================
# SECTION 5: CASH FLOW ANALYSIS
# ============================================================================
print("5. CASH FLOW ANALYSIS")
print("-" * 80)
print(f"Average Daily Income: EUR {total_income / max(days_span, 1):.2f}")
print(f"Average Daily Expenses: EUR {total_expenses / max(days_span, 1):.2f}")
print(f"Average Daily Net Flow: EUR {net_balance / max(days_span, 1):.2f}")

# Transaction frequency
print(f"\nTransaction Frequency:")
print(f"  Total Transactions: {num_transactions}")
print(f"  Average per Day: {num_transactions / max(days_span, 1):.1f}")
print(f"  Average per Month: {num_transactions / max(months_span, 1):.0f}")

# Income vs Expense frequency
print(f"  Income Transactions: {len(income_tx)} ({(len(income_tx)/num_transactions)*100:.1f}%)")
print(f"  Expense Transactions: {len(expense_tx)} ({(len(expense_tx)/num_transactions)*100:.1f}%)")
print()

# ============================================================================
# SECTION 6: CATEGORY RISK ASSESSMENT
# ============================================================================
print("6. CATEGORY RISK ASSESSMENT")
print("-" * 80)
print("High-Risk Categories (>20% of total expenses):")
high_risk = []
for cat, row in expense_by_cat.iterrows():
    pct = (row['sum'] / total_expenses) * 100
    if pct > 20:
        risk_level = "CRITICAL" if pct > 40 else "HIGH"
        high_risk.append((cat, row['sum'], pct, risk_level))
        print(f"  [{risk_level}] {cat}: EUR {row['sum']:,.2f} ({pct:.1f}%)")

if not high_risk:
    print("  No high-risk categories identified")

print("\nModerate-Risk Categories (10-20% of total expenses):")
moderate_risk = []
for cat, row in expense_by_cat.iterrows():
    pct = (row['sum'] / total_expenses) * 100
    if 10 <= pct <= 20:
        moderate_risk.append((cat, row['sum'], pct))
        print(f"  {cat}: EUR {row['sum']:,.2f} ({pct:.1f}%)")

if not moderate_risk:
    print("  No moderate-risk categories identified")
print()

# ============================================================================
# SECTION 7: ANOMALY DETECTION
# ============================================================================
print("7. ANOMALY DETECTION & UNUSUAL TRANSACTIONS")
print("-" * 80)

# Find large transactions
large_threshold = expense_tx['amount'].quantile(0.90)
large_expenses = expense_tx[expense_tx['amount'] > large_threshold].sort_values('amount', ascending=False)

print(f"Large Transactions (Top 10% by amount, threshold: EUR {large_threshold:.2f}):")
for idx, row in large_expenses.head(10).iterrows():
    print(f"  {row['date'].strftime('%d %b %Y')} | {row['description']}: EUR {row['amount']:.2f}")

# Find unusual patterns
print(f"\nTransaction Patterns:")
daily_tx = tx.groupby(tx['date'].dt.date)['amount'].agg(['count', 'sum'])
print(f"  Busiest Day: {daily_tx['count'].max()} transactions (EUR {daily_tx['sum'].max():.2f})")
print(f"  Quietest Day: {daily_tx['count'].min()} transactions (EUR {daily_tx['sum'].min():.2f})")
print(f"  Average Daily Transactions: {daily_tx['count'].mean():.1f}")

# Recurring patterns
print(f"\nRecurring Expense Patterns:")
recurring = expense_tx.groupby('description')['amount'].agg(['sum', 'count']).sort_values('count', ascending=False)
recurring_items = recurring[recurring['count'] >= 3].head(10)
for desc, row in recurring_items.iterrows():
    if len(desc) > 50:
        desc = desc[:47] + "..."
    print(f"  {desc}: EUR {row['sum']:.2f} ({int(row['count'])} occurrences)")
print()

# ============================================================================
# SECTION 8: FINANCIAL HEALTH SCORING
# ============================================================================
print("8. FINANCIAL HEALTH SCORE")
print("-" * 80)

scores = {}

# Income Stability (0-25 points)
income_cv = monthly_income.std() / monthly_income.mean() if monthly_income.mean() > 0 else 0
if income_cv < 0.1:
    income_score = 25
elif income_cv < 0.3:
    income_score = 20
elif income_cv < 0.5:
    income_score = 15
else:
    income_score = 10
scores['Income Stability'] = income_score
print(f"✓ Income Stability: {income_score}/25 (Coefficient of Variation: {income_cv:.2f})")

# Savings Rate (0-25 points)
if savings_rate >= 20:
    savings_score = 25
elif savings_rate >= 15:
    savings_score = 20
elif savings_rate >= 10:
    savings_score = 15
elif savings_rate >= 0:
    savings_score = 10
else:
    savings_score = 0
scores['Savings Rate'] = savings_score
print(f"✓ Savings Rate: {savings_score}/25 (Rate: {savings_rate:.1f}%)")

# Expense Control (0-25 points)
if not high_risk:
    expense_score = 25
elif len(high_risk) == 1:
    expense_score = 15
else:
    expense_score = 5
scores['Expense Control'] = expense_score
print(f"✓ Expense Control: {expense_score}/25 (High-risk categories: {len(high_risk)})")

# Emergency Fund (0-25 points)
emergency_score = min(25, int((0 / target_emergency_fund) * 25)) if target_emergency_fund > 0 else 0
scores['Emergency Fund'] = emergency_score
print(f"✓ Emergency Fund: {emergency_score}/25 (EUR {0:.2f} of EUR {target_emergency_fund:.2f})")

overall_score = sum(scores.values())
print(f"\n{'='*50}")
print(f"OVERALL FINANCIAL HEALTH SCORE: {overall_score}/100")
print(f"{'='*50}")

if overall_score >= 80:
    health_status = "EXCELLENT"
    color = "🟢"
elif overall_score >= 60:
    health_status = "GOOD"
    color = "🟢"
elif overall_score >= 40:
    health_status = "FAIR"
    color = "🟡"
else:
    health_status = "POOR"
    color = "🔴"

print(f"Health Status: {color} {health_status}")
print()

# ============================================================================
# SECTION 9: KEY ALERTS & WARNINGS
# ============================================================================
print("9. KEY ALERTS & WARNINGS")
print("-" * 80)

alerts = []

if net_balance < 0:
    alerts.append("🔴 CRITICAL: Negative net balance - spending exceeds income")
elif savings_rate < 5:
    alerts.append("🔴 CRITICAL: Very low savings rate (<5%)")

if len(high_risk) > 0:
    alerts.append(f"⚠️  WARNING: {len(high_risk)} high-risk expense category/categories (>20% of budget)")

if emergency_score == 0:
    alerts.append("⚠️  WARNING: No emergency fund - vulnerable to unexpected expenses")

if savings_rate < 10:
    alerts.append("⚠️  WARNING: Savings rate below recommended 10-15%")

# Check for extreme daily spending
daily_spend = expense_tx.groupby(expense_tx['date'].dt.date)['amount'].sum()
extreme_day = daily_spend.max()
if extreme_day > avg_monthly_expense / 3:
    alerts.append(f"⚠️  WARNING: Extreme spending detected (EUR {extreme_day:.2f} on single day)")

if len(alerts) == 0:
    print("✓ No critical alerts - account status is healthy")
else:
    for alert in alerts:
        print(alert)
print()

# ============================================================================
# SECTION 10: RECOMMENDATIONS
# ============================================================================
print("10. STRATEGIC RECOMMENDATIONS")
print("-" * 80)

recommendations = []

if savings_rate < 10:
    cut_amount = total_expenses * 0.15
    recommendations.append(f"1. INCREASE SAVINGS: Reduce discretionary spending by 15% to save EUR {cut_amount:.2f}/month")

for cat, amount, pct, risk in high_risk:
    reduction = amount * 0.20
    recommendations.append(f"2. OPTIMIZE '{cat}': Reduce spending by 20% (EUR {reduction:.2f}/month) - currently {pct:.0f}% of budget")

if emergency_score < 15:
    recommendations.append(f"3. BUILD EMERGENCY FUND: Target EUR {target_emergency_fund:.2f} (3 months expenses)")

# Check specific high-spend categories
for cat, row in expense_by_cat.head(5).iterrows():
    if row['count'] > 20:
        avg_tx = row['sum'] / row['count']
        recommendations.append(f"4. REVIEW '{cat}': {int(row['count'])} transactions averaging EUR {avg_tx:.2f} - look for consolidation opportunities")

if len(recommendations) == 0:
    print("✓ Your account is well-managed. Continue current spending patterns.")
else:
    for rec in recommendations[:5]:
        print(rec)
print()

# ============================================================================
# SECTION 11: SPENDING OPTIMIZATION OPPORTUNITIES
# ============================================================================
print("11. SPENDING OPTIMIZATION OPPORTUNITIES")
print("-" * 80)

total_optimizable = 0
optimization_plan = []

# Analyze each category for potential savings
for cat, row in expense_by_cat.iterrows():
    if row['count'] > 10:  # Only categories with enough transactions
        avg_tx = row['sum'] / row['count']
        std_tx = expense_tx[expense_tx['category'] == cat]['amount'].std()
        
        # If there's high variance, potential for better budgeting
        if std_tx > avg_tx * 0.5:
            potential_saving = row['sum'] * 0.10
            optimization_plan.append((cat, row['sum'], row['count'], potential_saving))
            total_optimizable += potential_saving

if optimization_plan:
    print("Categories with highest optimization potential:")
    for cat, total, count, saving in sorted(optimization_plan, key=lambda x: x[3], reverse=True)[:5]:
        print(f"  {cat}: EUR {saving:.2f}/month potential saving ({(saving/total)*100:.1f}% reduction)")
    print(f"\nTotal Potential Savings: EUR {total_optimizable:.2f}/month")
else:
    print("✓ Spending patterns are well-optimized.")
print()

# ============================================================================
# SECTION 12: MONTHLY PROJECTIONS
# ============================================================================
print("12. FINANCIAL PROJECTIONS (NEXT 6 MONTHS)")
print("-" * 80)

avg_monthly_income = monthly_income.mean()
avg_monthly_expense = monthly_expense.mean()
avg_monthly_net = avg_monthly_income - avg_monthly_expense

print(f"Based on average monthly patterns (Income EUR {avg_monthly_income:.2f}, Expenses EUR {avg_monthly_expense:.2f}):")
print()

projected_balance = 0
for month_num in range(1, 7):
    projected_balance += avg_monthly_net
    status = "✓" if projected_balance > 0 else "✗"
    print(f"  {status} Month +{month_num}: Projected Balance EUR {projected_balance:.2f}")

print()

# ============================================================================
# SECTION 13: COMPARATIVE BENCHMARKS
# ============================================================================
print("13. BENCHMARK COMPARISON (vs. European Averages)")
print("-" * 80)

print(f"Your Metrics                    | European Average    | Status")
print("-" * 70)
print(f"Savings Rate:        {savings_rate:6.1f}%          | 12.0%              | {'✗ Below' if savings_rate < 12 else '✓ Above'}")
print(f"Avg Monthly Expenses: EUR {avg_monthly_expense:7,.0f}     | EUR 2,000          | {'✓' if avg_monthly_expense < 2500 else '✗'}")
print(f"Emergency Fund Mo.:   {emergency_score/25*3:6.1f} months       | 3.0 months         | {'✗ Below' if emergency_score/25*3 < 3 else '✓ Above'}")
print()

print("=" * 80)
print("END OF REPORT")
print("=" * 80)
