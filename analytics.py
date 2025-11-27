import pandas as pd
import numpy as np
from datetime import datetime


def load_sample_data():
    tx = pd.read_csv('data/sample/transactions_sample.csv')
    acct = pd.read_csv('data/sample/accounts_sample.csv')
    return tx, acct


def analyze_finances(transactions_df: pd.DataFrame, accounts_df: pd.DataFrame):
    # Normalize columns
    df = transactions_df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'])
    df['type'] = df['type'].str.lower()
    df['category'] = df['category'].fillna('Uncategorized')

    # Income and expenses
    income = float(df[df['type'] == 'income']['amount'].sum())
    expenses = float(df[df['type'] == 'expense']['amount'].sum())
    savings_rate = (income - expenses) / income if income > 0 else 0

    # Category breakdown
    category_spend = (
        df[df['type'] == 'expense']
        .groupby('category')['amount']
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    # Overspending flags: top categories above 20% of total expenses
    total_expenses = max(expenses, 1e-9)
    category_spend['percent'] = category_spend['amount'] / total_expenses
    overspending = category_spend[category_spend['percent'] >= 0.20]

    # Accounts and emergency fund check
    acct = accounts_df.copy()
    acct['balance'] = pd.to_numeric(acct['balance'])
    liquid_savings = float(acct[acct['type'].isin(['cash', 'savings'])]['balance'].sum())
    monthly_expenses = float(df[(df['type'] == 'expense') & (df['date'] >= df['date'].max() - pd.DateOffset(months=1))]['amount'].sum())
    target_emergency = monthly_expenses * 3  # 3 months basic guideline
    has_emergency_fund = liquid_savings >= target_emergency

    # Alerts
    alerts = []
    if income <= expenses:
        alerts.append('Spending meets or exceeds income. Review budget urgently.')
    if not has_emergency_fund:
        alerts.append('No adequate emergency fund (3 months). Increase savings.')
    if savings_rate < 0.10:
        alerts.append('Savings rate below 10%. Aim to raise gradually.')

    # Recommendations
    recommended_cut = min(0.15, (expenses - income) / expenses if expenses else 0)
    monthly_savings_gain = recommended_cut * expenses
    recommendations = [
        f"Reduce discretionary spend by {int(recommended_cut*100)}% to free €{monthly_savings_gain:,.0f}/month",
    ]

    # Simple benchmarks (dummy age group average 12%)
    benchmarks = {
        'your_savings_rate': float(round(savings_rate * 100, 1)),
        'age_group_average': 12.0,
    }

    # Prepare chart data for Plotly - convert all to native Python types
    # Build values list explicitly
    chart_values = []
    chart_values.append(float(income))
    chart_values.append(float(expenses))
    
    charts = {
        'income_vs_expenses': {
            'labels': ['Income', 'Expenses'],
            'data': chart_values,
        },
        'category_breakdown': {
            'labels': [str(x) for x in category_spend['category'].tolist()],
            'data': [float(x) for x in category_spend['amount'].tolist()],
        },
        'savings_progress': {
            'liquid_savings': float(liquid_savings),
            'target_emergency': float(target_emergency),
        },
    }
    
    # Convert overspending dataframe to dict with native types
    overspending_list = []
    for _, row in overspending.iterrows():
        overspending_list.append({
            'category': str(row['category']),
            'amount': float(row['amount']),
            'percent': float(row['percent'])
        })

    return {
        'income': float(income),
        'expenses': float(expenses),
        'savings_rate': float(savings_rate),
        'alerts': alerts,
        'recommendations': recommendations,
        'benchmarks': benchmarks,
        'overspending': overspending_list,
        'charts': charts,
    }
