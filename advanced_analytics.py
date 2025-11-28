"""
Enhanced analytics engine with advanced insights, trends, and predictions.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import re


def detect_recurring_transactions(df, min_occurrences=3, tolerance_days=3):
    """
    Detect recurring transactions (subscriptions, bills, etc.)
    
    Args:
        df: Transaction DataFrame
        min_occurrences: Minimum number of times to be considered recurring
        tolerance_days: Days of tolerance for matching (e.g., monthly ±3 days)
    
    Returns:
        List of recurring transaction patterns
    """
    recurring = []
    expense_df = df[df['type'] == 'expense'].copy()
    
    # Group by similar amounts and descriptions
    for desc in expense_df['description'].unique():
        # Escape special regex characters
        desc_pattern = re.escape(desc[:20])
        desc_txs = expense_df[expense_df['description'].str.contains(desc_pattern, case=False, na=False, regex=True)]
        
        if len(desc_txs) >= min_occurrences:
            # Check if amounts are similar
            amounts = desc_txs['amount'].values
            avg_amount = float(np.mean(amounts))
            std_amount = float(np.std(amounts))
            
            if std_amount / avg_amount < 0.1:  # Less than 10% variation
                # Check if dates are regularly spaced
                dates = sorted(desc_txs['date'].tolist())
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                
                if len(intervals) > 0:
                    avg_interval = np.mean(intervals)
                    std_interval = np.std(intervals)
                    
                    # If intervals are consistent (monthly ~30 days, weekly ~7 days)
                    if std_interval < tolerance_days:
                        frequency = 'Monthly' if 25 <= avg_interval <= 35 else \
                                  'Weekly' if 5 <= avg_interval <= 9 else \
                                  'Bi-weekly' if 12 <= avg_interval <= 16 else \
                                  f'Every {int(avg_interval)} days'
                        
                        next_due = dates[-1] + timedelta(days=int(avg_interval))
                        
                        recurring.append({
                            'description': desc[:50],
                            'amount': avg_amount,
                            'frequency': frequency,
                            'occurrences': len(desc_txs),
                            'last_date': dates[-1].strftime('%Y-%m-%d'),
                            'next_due': next_due.strftime('%Y-%m-%d') if next_due > datetime.now() else 'Overdue',
                            'avg_interval_days': int(avg_interval)
                        })
    
    return sorted(recurring, key=lambda x: x['amount'], reverse=True)


def calculate_monthly_trends(df, num_months=6):
    """
    Calculate spending and income trends over time.
    
    Returns:
        Dictionary with monthly trends data
    """
    df = df.copy()
    df['month'] = df['date'].dt.to_period('M')
    
    # Group by month and type
    monthly_summary = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
    
    # Get last N months
    if len(monthly_summary) > num_months:
        monthly_summary = monthly_summary.tail(num_months)
    
    months = [str(m) for m in monthly_summary.index]
    income_trend = [float(x) for x in monthly_summary.get('income', pd.Series([0]*len(months))).values]
    expense_trend = [float(x) for x in monthly_summary.get('expense', pd.Series([0]*len(months))).values]
    
    # Calculate month-over-month changes
    mom_income_change = 0.0
    mom_expense_change = 0.0
    
    if len(income_trend) >= 2:
        if income_trend[-2] > 0:
            mom_income_change = ((income_trend[-1] - income_trend[-2]) / income_trend[-2]) * 100
        if expense_trend[-2] > 0:
            mom_expense_change = ((expense_trend[-1] - expense_trend[-2]) / expense_trend[-2]) * 100
    
    return {
        'months': months,
        'income': income_trend,
        'expenses': expense_trend,
        'savings': [float(i - e) for i, e in zip(income_trend, expense_trend)],
        'mom_income_change': float(mom_income_change),
        'mom_expense_change': float(mom_expense_change)
    }


def predict_next_month(monthly_trends):
    """
    Simple linear prediction for next month's expenses.
    """
    expenses = monthly_trends['expenses']
    
    if len(expenses) < 2:
        return {
            'predicted_expenses': expenses[-1] if expenses else 0,
            'confidence': 'Low'
        }
    
    # Simple linear regression
    x = np.arange(len(expenses))
    y = np.array(expenses)
    
    # Handle edge case
    if len(x) != len(y):
        return {
            'predicted_expenses': float(expenses[-1]),
            'confidence': 'Low'
        }
    
    slope, intercept = np.polyfit(x, y, 1)
    predicted = float(slope * len(expenses) + intercept)
    
    # Calculate confidence based on R²
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    confidence = 'High' if r_squared > 0.7 else 'Medium' if r_squared > 0.4 else 'Low'
    
    return {
        'predicted_expenses': max(0, predicted),
        'trend': 'Increasing' if slope > 0 else 'Decreasing',
        'confidence': confidence,
        'r_squared': float(r_squared)
    }


def analyze_category_trends(df, top_n=5):
    """
    Analyze spending trends by category.
    """
    expense_df = df[df['type'] == 'expense'].copy()
    expense_df['month'] = expense_df['date'].dt.to_period('M')
    
    # Get top categories
    top_categories = (
        expense_df.groupby('category')['amount']
        .sum()
        .nlargest(top_n)
        .index.tolist()
    )
    
    category_trends = {}
    for cat in top_categories:
        cat_data = expense_df[expense_df['category'] == cat]
        monthly = cat_data.groupby('month')['amount'].sum()
        
        category_trends[cat] = {
            'months': [str(m) for m in monthly.index],
            'amounts': [float(x) for x in monthly.values],
            'total': float(cat_data['amount'].sum()),
            'avg_monthly': float(monthly.mean())
        }
    
    return category_trends


def calculate_budget_status(df, budgets):
    """
    Compare spending against budgets.
    
    Args:
        df: Transaction DataFrame
        budgets: Dict of category budgets {category: amount}
    
    Returns:
        Budget status for each category
    """
    expense_df = df[df['type'] == 'expense'].copy()
    latest_month = expense_df['date'].max().to_period('M')
    current_month_df = expense_df[expense_df['date'].dt.to_period('M') == latest_month]
    
    spending = current_month_df.groupby('category')['amount'].sum().to_dict()
    
    budget_status = []
    for category, budget in budgets.items():
        spent = float(spending.get(category, 0))
        remaining = float(budget - spent)
        percent_used = float((spent / budget * 100) if budget > 0 else 0)
        
        status = 'over' if spent > budget else 'warning' if percent_used > 80 else 'good'
        
        budget_status.append({
            'category': category,
            'budget': float(budget),
            'spent': spent,
            'remaining': remaining,
            'percent_used': percent_used,
            'status': status
        })
    
    return sorted(budget_status, key=lambda x: x['percent_used'], reverse=True)


def detect_unusual_spending(df, threshold=2.0):
    """
    Detect unusual/anomalous transactions (outliers).
    
    Args:
        threshold: Number of standard deviations to consider unusual
    """
    expense_df = df[df['type'] == 'expense'].copy()
    
    unusual = []
    for category in expense_df['category'].unique():
        cat_df = expense_df[expense_df['category'] == category]
        
        if len(cat_df) < 3:
            continue
        
        mean_amount = cat_df['amount'].mean()
        std_amount = cat_df['amount'].std()
        
        if std_amount == 0:
            continue
        
        outliers = cat_df[cat_df['amount'] > mean_amount + threshold * std_amount]
        
        for _, row in outliers.iterrows():
            unusual.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'category': row['category'],
                'description': row.get('description', 'Unknown')[:50],
                'amount': float(row['amount']),
                'typical_amount': float(mean_amount),
                'deviation': float((row['amount'] - mean_amount) / std_amount)
            })
    
    return sorted(unusual, key=lambda x: x['deviation'], reverse=True)[:10]


def calculate_savings_goals(current_savings, monthly_savings, goals):
    """
    Calculate progress and time to reach savings goals.
    
    Args:
        current_savings: Current total savings
        monthly_savings: Average monthly savings amount
        goals: List of goal dicts with 'name', 'target', 'deadline' (optional)
    """
    goal_progress = []
    
    for goal in goals:
        target = goal['target']
        remaining = target - current_savings
        
        if monthly_savings > 0:
            months_needed = remaining / monthly_savings
            projected_date = (datetime.now() + timedelta(days=months_needed * 30)).strftime('%Y-%m-%d')
        else:
            months_needed = float('inf')
            projected_date = 'Unknown'
        
        progress_percent = (current_savings / target * 100) if target > 0 else 0
        
        status = 'achieved' if current_savings >= target else \
                'on_track' if months_needed < 12 else \
                'at_risk' if months_needed < 24 else 'off_track'
        
        goal_progress.append({
            'name': goal['name'],
            'target': float(target),
            'current': float(current_savings),
            'remaining': float(max(0, remaining)),
            'progress_percent': float(min(100, progress_percent)),
            'months_needed': float(months_needed) if months_needed != float('inf') else None,
            'projected_date': projected_date,
            'status': status
        })
    
    return goal_progress


def analyze_spending_optimization(df, num_months=6):
    """
    Analyze spending patterns to identify cost-cutting opportunities and savings increase strategies.
    
    Args:
        df: Transaction DataFrame with date, amount, type, category, description
        num_months: Number of recent months to analyze
        
    Returns:
        Dictionary with month-by-month comparison and optimization recommendations
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['month'] = df['date'].dt.to_period('M')
    
    # Get last N months
    recent_months = sorted(df['month'].unique())[-num_months:]
    df_recent = df[df['month'].isin(recent_months)]
    
    # Monthly expense breakdown by category
    monthly_category_spend = df_recent[df_recent['type'] == 'expense'].groupby(['month', 'category'])['amount'].sum().reset_index()
    
    # Calculate category averages and identify overspending
    category_stats = []
    for category in df_recent[df_recent['type'] == 'expense']['category'].unique():
        cat_data = monthly_category_spend[monthly_category_spend['category'] == category]
        
        if len(cat_data) > 0:
            amounts = cat_data['amount'].values
            avg_spend = float(np.mean(amounts))
            max_spend = float(np.max(amounts))
            min_spend = float(np.min(amounts))
            std_spend = float(np.std(amounts)) if len(amounts) > 1 else 0
            
            # Identify potential savings (difference between max and minimum)
            potential_savings = max_spend - min_spend
            
            # Calculate variability (high variability = room for optimization)
            variability = (std_spend / avg_spend * 100) if avg_spend > 0 else 0
            
            # Flag categories with high variability or consistently high spending
            is_optimizable = variability > 30 or avg_spend > 200
            
            category_stats.append({
                'category': category,
                'avg_monthly': avg_spend,
                'min_monthly': min_spend,
                'max_monthly': max_spend,
                'std_dev': std_spend,
                'variability_percent': variability,
                'potential_monthly_savings': potential_savings / len(amounts),
                'is_optimizable': is_optimizable,
                'months_analyzed': len(amounts)
            })
    
    # Sort by potential savings (highest first)
    category_stats = sorted(category_stats, key=lambda x: x['potential_monthly_savings'], reverse=True)
    
    # Month-over-month comparison
    monthly_totals = []
    for month in recent_months:
        month_data = df_recent[df_recent['month'] == month]
        income = float(month_data[month_data['type'] == 'income']['amount'].sum())
        expenses = float(month_data[month_data['type'] == 'expense']['amount'].sum())
        savings = income - expenses
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        monthly_totals.append({
            'month': str(month),
            'income': income,
            'expenses': expenses,
            'savings': savings,
            'savings_rate': savings_rate
        })
    
    # Calculate trends
    if len(monthly_totals) >= 2:
        expense_trend = monthly_totals[-1]['expenses'] - monthly_totals[0]['expenses']
        savings_trend = monthly_totals[-1]['savings'] - monthly_totals[0]['savings']
    else:
        expense_trend = 0
        savings_trend = 0
    
    # Generate actionable recommendations
    recommendations = []
    
    # Top 3 categories to optimize
    top_optimizable = [c for c in category_stats if c['is_optimizable']][:3]
    for cat in top_optimizable:
        if cat['variability_percent'] > 50:
            recommendations.append({
                'type': 'reduce_variability',
                'category': cat['category'],
                'priority': 'high',
                'message': f"Your {cat['category']} spending varies significantly (±{cat['variability_percent']:.0f}%). "
                          f"If you can consistently spend closer to your minimum of €{cat['min_monthly']:.2f}, "
                          f"you could save €{cat['potential_monthly_savings']:.2f}/month.",
                'potential_savings': cat['potential_monthly_savings']
            })
        elif cat['avg_monthly'] > 200:
            recommendations.append({
                'type': 'reduce_high_spending',
                'category': cat['category'],
                'priority': 'medium',
                'message': f"{cat['category']} averages €{cat['avg_monthly']:.2f}/month. "
                          f"Reducing by 20% could save €{cat['avg_monthly'] * 0.2:.2f}/month.",
                'potential_savings': cat['avg_monthly'] * 0.2
            })
    
    # Income recommendations
    avg_income = np.mean([m['income'] for m in monthly_totals]) if monthly_totals else 0
    avg_expenses = np.mean([m['expenses'] for m in monthly_totals]) if monthly_totals else 0
    
    if avg_income > 0 and (avg_expenses / avg_income) > 0.8:
        recommendations.append({
            'type': 'increase_income',
            'category': 'Income',
            'priority': 'high',
            'message': f"Your expense-to-income ratio is high ({avg_expenses/avg_income*100:.0f}%). "
                      f"Consider supplementary income sources or negotiating a raise.",
            'potential_savings': 0
        })
    
    # Calculate total potential monthly savings
    total_potential_savings = sum([r['potential_savings'] for r in recommendations])
    
    # Calculate what savings rate could be with optimization
    current_avg_savings = avg_income - avg_expenses
    optimized_savings = current_avg_savings + total_potential_savings
    optimized_savings_rate = (optimized_savings / avg_income * 100) if avg_income > 0 else 0
    current_savings_rate = (current_avg_savings / avg_income * 100) if avg_income > 0 else 0
    
    return {
        'monthly_comparison': monthly_totals,
        'category_analysis': category_stats[:10],  # Top 10 categories
        'recommendations': recommendations,
        'summary': {
            'avg_monthly_income': float(avg_income),
            'avg_monthly_expenses': float(avg_expenses),
            'avg_monthly_savings': float(current_avg_savings),
            'current_savings_rate': float(current_savings_rate),
            'total_potential_monthly_savings': float(total_potential_savings),
            'optimized_monthly_savings': float(optimized_savings),
            'optimized_savings_rate': float(optimized_savings_rate),
            'improvement_percent': float(optimized_savings_rate - current_savings_rate),
            'expense_trend': 'increasing' if expense_trend > 0 else 'decreasing' if expense_trend < 0 else 'stable',
            'savings_trend': 'improving' if savings_trend > 0 else 'declining' if savings_trend < 0 else 'stable'
        }
    }
