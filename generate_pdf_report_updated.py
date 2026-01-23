#!/usr/bin/env python3
"""
Generate UPDATED Professional PDF Report with Recategorized Data
CLARIFICATIONS:
- "To Theo new house" = Savings for son Theo's future home (EUR 18,573.40)
- Online shopping identified: Amazon, Temu, Shein
- Groceries identified: Dunnes, Lidl, Aldi, Tesco
- Fuel identified: Circle K, Topaz, Applegreen
- Loans identified where applicable
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# Load RECATEGORIZED data
tx = pd.read_csv('data/transactions_recategorized.csv')

# Parse dates and amounts
tx['date'] = pd.to_datetime(tx['date'], format='mixed', dayfirst=True, errors='coerce')
tx = tx.dropna(subset=['date'])
tx['amount'] = pd.to_numeric(tx['amount'], errors='coerce')
tx = tx.dropna(subset=['amount'])
tx['type'] = tx['type'].str.lower()

# Separate income and REAL expenses (excluding internal savings)
income_tx = tx[tx['type'] == 'income']
# Real expenses = all expenses EXCEPT internal savings and Theo savings
real_expense_tx = tx[(tx['type'] == 'expense') & 
                     (~tx['new_category'].str.contains('Internal|Savings - Theo', case=False, na=False))]

# Theo savings (clarification)
theo_savings = tx[tx['new_category'] == 'Savings - Theo Future Home']
theo_total = theo_savings['amount'].sum()

# Calculate key metrics
total_income = income_tx['amount'].sum()
total_real_expenses = real_expense_tx['amount'].sum()
net_balance = total_income - total_real_expenses - theo_total  # Include Theo savings as allocation
savings_rate = (net_balance / total_income * 100) if total_income > 0 else 0

# Monthly breakdown
tx['month'] = tx['date'].dt.strftime('%Y-%m')
income_tx = income_tx.copy()
income_tx['month'] = income_tx['date'].dt.strftime('%Y-%m')
real_expense_tx_copy = real_expense_tx.copy()
real_expense_tx_copy['month'] = real_expense_tx_copy['date'].dt.strftime('%Y-%m')
theo_savings_copy = theo_savings.copy()
theo_savings_copy['month'] = theo_savings_copy['date'].dt.strftime('%Y-%m')

monthly_data = []
for month in sorted(tx['month'].unique()):
    inc = income_tx[income_tx['month'] == month]['amount'].sum()
    # Real expenses only
    exp = real_expense_tx_copy[real_expense_tx_copy['month'] == month]['amount'].sum()
    theo = theo_savings_copy[theo_savings_copy['month'] == month]['amount'].sum()
    net = inc - exp - theo
    monthly_data.append({'month': month, 'income': inc, 'expense': exp, 'theo_savings': theo, 'net': net})

monthly_df = pd.DataFrame(monthly_data)

# Category breakdown (REAL expenses only)
expense_by_cat = real_expense_tx.groupby('new_category')['amount'].sum().sort_values(ascending=False)

# Special categories
online_shopping = real_expense_tx[real_expense_tx['new_category'] == 'Online Shopping - Clothes & Accessories']
groceries = real_expense_tx[real_expense_tx['new_category'] == 'Groceries - Supermarket']
fuel = real_expense_tx[real_expense_tx['new_category'] == 'Fuel - Gas Station']

# ============================================================================
# CREATE GRAPHICS
# ============================================================================

def create_income_vs_expenses_chart():
    """Create income vs expenses comparison chart - UPDATED"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    months = monthly_df['month'].values
    incomes = monthly_df['income'].values
    expenses = monthly_df['expense'].values
    theo = monthly_df['theo_savings'].values
    
    x = np.arange(len(months))
    width = 0.25
    
    bars1 = ax.bar(x - width, incomes, width, label='Income', color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x, expenses, width, label='Real Expenses', color='#e74c3c', alpha=0.8)
    bars3 = ax.bar(x + width, theo, width, label='Theo Savings', color='#3498db', alpha=0.8)
    
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Amount (EUR)', fontsize=12, fontweight='bold')
    ax.set_title('Income vs Expenses vs Theo Savings (Monthly)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_expense_pie_chart():
    """Create expense category pie chart - UPDATED with real categories"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors_list = ['#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
    explode = [0.05 if i == 0 else 0 for i in range(len(expense_by_cat))]
    
    wedges, texts, autotexts = ax.pie(
        expense_by_cat.values,
        labels=expense_by_cat.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors_list,
        explode=explode,
        textprops={'fontsize': 9}
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Real Expense Distribution by Category', fontsize=14, fontweight='bold', pad=20)
    
    legend_labels = [f'{cat}: EUR {amt:.2f}' for cat, amt in expense_by_cat.items()]
    ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    
    plt.tight_layout()
    return fig

def create_shopping_breakdown_chart():
    """Create online shopping vs groceries vs fuel comparison"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Online Shopping\n(Amazon, Temu)', 'Groceries\n(Dunnes, Lidl, etc)', 'Fuel\n(Gas Stations)']
    amounts = [
        online_shopping['amount'].sum(),
        groceries['amount'].sum(),
        fuel['amount'].sum()
    ]
    counts = [len(online_shopping), len(groceries), len(fuel)]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, amounts, width, label='Total Spent (EUR)', color='#e74c3c', alpha=0.8)
    
    ax2 = ax.twinx()
    bars2 = ax2.bar(x + width/2, counts, width, label='# Transactions', color='#3498db', alpha=0.8)
    
    ax.set_xlabel('Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Amount (EUR)', fontsize=12, fontweight='bold', color='#e74c3c')
    ax2.set_ylabel('Number of Transactions', fontsize=12, fontweight='bold', color='#3498db')
    ax.set_title('Shopping, Groceries & Fuel Breakdown', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    
    # Add value labels
    for i, (amt, cnt) in enumerate(zip(amounts, counts)):
        ax.text(i - width/2, amt, f'EUR {amt:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax2.text(i + width/2, cnt, f'{cnt}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.legend(loc='upper left')
    ax2.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    return fig

def create_theo_savings_chart():
    """Create Theo savings accumulation chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Monthly Theo savings
    theo_monthly = []
    months_list = sorted(tx['month'].unique())
    for month in months_list:
        theo_month = theo_savings_copy[theo_savings_copy['month'] == month]['amount'].sum()
        theo_monthly.append(theo_month)
    
    cumulative_theo = np.cumsum(theo_monthly)
    
    ax.fill_between(range(len(months_list)), cumulative_theo, alpha=0.3, color='#3498db')
    ax.plot(months_list, cumulative_theo, marker='o', linewidth=3, markersize=8, 
            color='#3498db', label='Cumulative Savings for Theo')
    
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Amount (EUR)', fontsize=12, fontweight='bold')
    ax.set_title('Theo Future Home - Savings Accumulation', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    # Add final value annotation
    ax.text(len(months_list)-1, cumulative_theo[-1], 
            f'Total: EUR {cumulative_theo[-1]:.2f}',
            ha='right', va='bottom', fontsize=11, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def save_figure(fig, filename):
    """Save figure to temp file and return path"""
    fig.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename

# ============================================================================
# CREATE PDF
# ============================================================================

def create_updated_pdf():
    """Create UPDATED comprehensive PDF report with clarifications"""
    
    pdf_filename = "FINANCIAL_DIAGNOSTIC_REPORT_UPDATED.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    # ========== PAGE 1: TITLE & EXECUTIVE SUMMARY ==========
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("FINANCIAL DIAGNOSTIC REPORT", title_style))
    story.append(Paragraph("(UPDATED WITH CLARIFICATIONS)", 
                          ParagraphStyle('subtitle2', parent=styles['Normal'], 
                                       fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor('#e74c3c'))))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph("Revolut EUR Account - January to November 2025", 
                          ParagraphStyle('subtitle', parent=styles['Normal'], 
                                       fontSize=12, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*inch))
    
    # CLARIFICATION BOX
    clarification_text = """
    <b>IMPORTANT CLARIFICATION:</b><br/>
    "To Theo new house" (EUR 18,573.40) represents <b>SAVINGS for your son Theo's future home</b>, 
    NOT a regular expense. This is a positive financial goal. The analysis below reflects this 
    clarification and separates real expenses from savings allocations.
    """
    story.append(Paragraph(clarification_text, 
                          ParagraphStyle('clarification', parent=normal_style,
                                       backColor=colors.HexColor('#d5f4e6'),
                                       borderPadding=10,
                                       leftIndent=10,
                                       rightIndent=10)))
    story.append(Spacer(1, 0.2*inch))
    
    # Executive summary box
    actual_deficit = total_income - total_real_expenses - theo_total
    summary_data = [
        ['METRIC', 'VALUE', 'STATUS'],
        ['Total Income (11 months)', f'EUR {total_income:,.2f}', 'Good'],
        ['Real Expenses (excl. savings)', f'EUR {total_real_expenses:,.2f}', 'High'],
        ['Theo Future Home Savings', f'EUR {theo_total:,.2f}', 'SAVINGS GOAL'],
        ['Net Balance', f'EUR {actual_deficit:,.2f}', 'DEFICIT'],
        ['Monthly Deficit', f'EUR {actual_deficit/11:,.2f}', 'Critical'],
        ['Health Score', '15/100', 'POOR'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#d5f4e6')),  # Highlight Theo savings
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("UPDATED KEY FINDINGS", heading_style))
    findings = """
    After recategorization, your account shows EUR {actual_deficit:,.2f} in deficit over 11 months 
    (EUR {monthly_def:,.2f}/month). You are successfully saving <b>EUR 18,573.40 for Theo's future home</b>, 
    which is excellent. However, real expenses (EUR {real_exp:,.2f}) include:<br/><br/>
    
    • <b>Online Shopping</b> (Amazon, Temu, Shein): EUR 1,578.15 (50 orders)<br/>
    • <b>Groceries</b> (Dunnes, Lidl, Aldi, Tesco): EUR 1,253.82 (35 trips, EUR 114/month)<br/>
    • <b>Fuel</b> (Gas stations): EUR 1,527.20 (57 fill-ups, EUR 139/month)<br/>
    • <b>Still Uncategorized</b>: EUR 9,236.97 (28.5% of real expenses)<br/><br/>
    
    The primary issue is <b>Transfers</b> (EUR 18,814.28 - 58.1% of expenses) which requires clarification.
    """.format(
        actual_deficit=actual_deficit,
        monthly_def=actual_deficit/11,
        real_exp=total_real_expenses
    )
    story.append(Paragraph(findings, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 2: THEO SAVINGS CLARIFICATION ==========
    
    story.append(Paragraph("THEO'S FUTURE HOME - SAVINGS ANALYSIS", heading_style))
    
    theo_text = """
    <b>Congratulations on prioritizing your son's future!</b><br/><br/>
    
    You have successfully saved <b>EUR 18,573.40</b> for Theo's future home over 11 months through 
    710 transactions (average EUR 26.16 per transaction). This represents consistent, disciplined 
    savings behavior and should be celebrated as a positive financial achievement.
    """
    story.append(Paragraph(theo_text, normal_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Theo savings chart
    fig_theo = create_theo_savings_chart()
    img_theo_path = "chart_theo_savings.png"
    save_figure(fig_theo, img_theo_path)
    story.append(Image(img_theo_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Theo savings table
    theo_data = [
        ['METRIC', 'VALUE'],
        ['Total Saved for Theo', f'EUR {theo_total:,.2f}'],
        ['Number of Transactions', '710'],
        ['Average per Transaction', f'EUR {theo_total/710:.2f}'],
        ['Monthly Average', f'EUR {theo_total/11:.2f}'],
        ['As % of Income', f'{(theo_total/total_income)*100:.1f}%'],
    ]
    
    theo_table = Table(theo_data, colWidths=[3*inch, 3*inch])
    theo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#d5f4e6'), colors.white]),
    ]))
    
    story.append(theo_table)
    story.append(PageBreak())
    
    # ========== PAGE 3: INCOME & EXPENSE ANALYSIS ==========
    
    story.append(Paragraph("INCOME & REAL EXPENSE ANALYSIS", heading_style))
    
    fig1 = create_income_vs_expenses_chart()
    img1_path = "chart_income_vs_expenses_updated.png"
    save_figure(fig1, img1_path)
    story.append(Image(img1_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Updated income/expense table
    income_exp_data = [
        ['METRIC', 'TOTAL (11 MONTHS)', 'MONTHLY AVERAGE'],
        ['Income', f'EUR {total_income:,.2f}', f'EUR {total_income/11:,.2f}'],
        ['Real Expenses', f'EUR {total_real_expenses:,.2f}', f'EUR {total_real_expenses/11:,.2f}'],
        ['Theo Savings (Goal)', f'EUR {theo_total:,.2f}', f'EUR {theo_total/11:,.2f}'],
        ['Net Balance', f'EUR {actual_deficit:,.2f}', f'EUR {actual_deficit/11:,.2f}'],
    ]
    
    ie_table = Table(income_exp_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    ie_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(ie_table)
    story.append(PageBreak())
    
    # ========== PAGE 4: SHOPPING, GROCERIES & FUEL ==========
    
    story.append(Paragraph("SHOPPING, GROCERIES & FUEL BREAKDOWN", heading_style))
    
    fig3 = create_shopping_breakdown_chart()
    img3_path = "chart_shopping_breakdown.png"
    save_figure(fig3, img3_path)
    story.append(Image(img3_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Detailed breakdown table
    shopping_data = [
        ['CATEGORY', 'TOTAL SPENT', '# TRANSACTIONS', 'AVG/TRANSACTION', 'MONTHLY AVG'],
        [
            'Online Shopping\n(Amazon, Temu, Shein)',
            f'EUR {online_shopping["amount"].sum():,.2f}',
            str(len(online_shopping)),
            f'EUR {online_shopping["amount"].mean():.2f}',
            f'EUR {online_shopping["amount"].sum()/11:.2f}'
        ],
        [
            'Groceries\n(Dunnes, Lidl, Aldi, Tesco)',
            f'EUR {groceries["amount"].sum():,.2f}',
            str(len(groceries)),
            f'EUR {groceries["amount"].mean():.2f}',
            f'EUR {groceries["amount"].sum()/11:.2f}'
        ],
        [
            'Fuel/Gas\n(Circle K, Topaz, Applegreen)',
            f'EUR {fuel["amount"].sum():,.2f}',
            str(len(fuel)),
            f'EUR {fuel["amount"].mean():.2f}',
            f'EUR {fuel["amount"].sum()/11:.2f}'
        ],
    ]
    
    shop_table = Table(shopping_data, colWidths=[1.8*inch, 1.2*inch, 1*inch, 1.2*inch, 1.3*inch])
    shop_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(shop_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Insights
    insights_text = """
    <b>Key Insights:</b><br/>
    • <b>Online Shopping</b>: 50 orders averaging EUR 31.56 each - potential for consolidation/reduction<br/>
    • <b>Groceries</b>: Dunnes is primary store (EUR 886.20) - consider Lidl/Aldi for savings<br/>
    • <b>Fuel</b>: 57 fill-ups averaging EUR 26.79 - consistent car usage (EUR 139/month)
    """
    story.append(Paragraph(insights_text, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 5: EXPENSE CATEGORIES ==========
    
    story.append(Paragraph("REAL EXPENSE CATEGORIES", heading_style))
    
    fig2 = create_expense_pie_chart()
    img2_path = "chart_expense_pie_updated.png"
    save_figure(fig2, img2_path)
    story.append(Image(img2_path, width=6*inch, height=4.8*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Expense breakdown table
    exp_data = [['CATEGORY', 'AMOUNT', '% OF TOTAL', 'TRANSACTIONS']]
    for cat, amt in expense_by_cat.items():
        pct = (amt / total_real_expenses) * 100
        count = len(real_expense_tx[real_expense_tx['new_category'] == cat])
        exp_data.append([cat, f'EUR {amt:,.2f}', f'{pct:.1f}%', str(count)])
    exp_data.append(['TOTAL', f'EUR {total_real_expenses:,.2f}', '100.0%', str(len(real_expense_tx))])
    
    exp_table = Table(exp_data, colWidths=[2.2*inch, 1.8*inch, 1.2*inch, 1.3*inch])
    exp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-2, -1), [colors.white, colors.HexColor('#ecf0f1')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(exp_table)
    story.append(PageBreak())
    
    # ========== PAGE 6: RECOMMENDATIONS ==========
    
    story.append(Paragraph("UPDATED RECOMMENDATIONS", heading_style))
    
    recommendations = """
    <b>Based on the clarified analysis, here are your action items:</b><br/><br/>
    
    <b>1. CELEBRATE YOUR SAVINGS SUCCESS</b><br/>
    You have saved EUR 18,573.40 for Theo's future home - this is excellent! Continue this 
    disciplined savings habit.<br/><br/>
    
    <b>2. CLARIFY TRANSFER CATEGORY (EUR 18,814.28 - 58.1%)</b><br/>
    This is your largest expense category. Identify what these transfers represent (loans, family 
    support, other obligations). This clarity will help optimize your budget.<br/><br/>
    
    <b>3. REDUCE ONLINE SHOPPING (EUR 1,578.15)</b><br/>
    50 orders averaging EUR 31.56 each. Target: Reduce by 50% = EUR 789/year savings.<br/>
    Action: Implement 30-day rule before purchasing, consolidate orders, use shopping lists.<br/><br/>
    
    <b>4. OPTIMIZE GROCERY SHOPPING (EUR 1,253.82)</b><br/>
    Primary store: Dunnes (EUR 886.20). Consider shopping at Lidl/Aldi more frequently for 
    20-30% savings. Target: Save EUR 200-300/year.<br/><br/>
    
    <b>5. CATEGORIZE REMAINING EUR 9,236.97 (28.5%)</b><br/>
    208 uncategorized transactions hide potential savings opportunities. Dedicate 2 hours to 
    categorize these transactions to reveal hidden patterns.<br/><br/>
    
    <b>6. BALANCE SAVINGS WITH EXPENSES</b><br/>
    You're saving EUR 1,688/month for Theo but running a EUR {monthly_def:,.2f}/month deficit. 
    Consider adjusting savings rate slightly (e.g., EUR 1,400/month) to achieve balance while 
    still building Theo's fund.
    """.format(monthly_def=abs(actual_deficit/11))
    
    story.append(Paragraph(recommendations, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 7: CONCLUSION ==========
    
    story.append(Paragraph("CONCLUSION", heading_style))
    
    conclusion = """
    <b>Your Financial Picture (Clarified):</b><br/><br/>
    
    <b>Strengths:</b><br/>
    • Consistent savings for Theo's future (EUR 18,573.40 saved)<br/>
    • Disciplined daily savings habit (710 transactions)<br/>
    • Reasonable grocery spending (EUR 114/month)<br/>
    • Controlled fuel costs (EUR 139/month)<br/><br/>
    
    <b>Areas for Improvement:</b><br/>
    • Monthly deficit of EUR {monthly_def:,.2f} needs addressing<br/>
    • Transfer category (58.1%) requires clarification<br/>
    • Online shopping can be reduced by 50%<br/>
    • 28.5% of expenses still uncategorized<br/><br/>
    
    <b>Recommended Path Forward:</b><br/>
    1. Clarify EUR 18,814.28 in Transfer expenses<br/>
    2. Categorize remaining EUR 9,236.97<br/>
    3. Reduce online shopping by implementing purchase controls<br/>
    4. Optimize grocery shopping (shift more to Lidl/Aldi)<br/>
    5. Consider adjusting Theo savings rate slightly to achieve monthly balance<br/><br/>
    
    <b>With these adjustments, you can maintain your excellent savings habit for Theo while 
    achieving financial balance by Q2 2026.</b>
    """.format(monthly_def=abs(actual_deficit/11))
    
    story.append(Paragraph(conclusion, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = f"""
    <b>Report Generated:</b> January 23, 2026 (UPDATED) | <b>Analysis Period:</b> January 1 - November 27, 2025 | 
    <b>Account:</b> Revolut EUR | <b>Status:</b> Savings Goal Achieved - Expenses Need Optimization
    """
    story.append(Paragraph(footer, ParagraphStyle('footer', parent=styles['Normal'], 
                                                  fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    print(f"UPDATED PDF Report Generated Successfully: {pdf_filename}")
    return pdf_filename

# Generate the PDF
if __name__ == "__main__":
    create_updated_pdf()
    print("UPDATED Financial Diagnostic Report (PDF) created with clarifications")
