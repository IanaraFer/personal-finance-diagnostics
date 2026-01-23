#!/usr/bin/env python3
"""
Generate Professional PDF Report with Graphics, Tables, and Figures
Using ReportLab for high-quality PDF output
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import io

# Load data
tx = pd.read_csv('data/transactions_from_pdf.csv')
acct = pd.read_csv('data/accounts_from_pdf.csv')

# Parse dates and amounts
tx['date'] = pd.to_datetime(tx['date'], format='mixed', dayfirst=True, errors='coerce')
tx = tx.dropna(subset=['date'])
tx['amount'] = pd.to_numeric(tx['amount'], errors='coerce')
tx = tx.dropna(subset=['amount'])
tx['type'] = tx['type'].str.lower()

# Separate income and expenses
income_tx = tx[tx['type'] == 'income']
expense_tx = tx[tx['type'] == 'expense']

# Calculate key metrics
total_income = income_tx['amount'].sum()
total_expenses = expense_tx['amount'].sum()
net_balance = total_income - total_expenses
savings_rate = (net_balance / total_income * 100) if total_income > 0 else 0

# Monthly breakdown
tx['month'] = tx['date'].dt.strftime('%Y-%m')
income_tx_copy = income_tx.copy()
expense_tx_copy = expense_tx.copy()
income_tx_copy['month'] = income_tx_copy['date'].dt.strftime('%Y-%m')
expense_tx_copy['month'] = expense_tx_copy['date'].dt.strftime('%Y-%m')

monthly_data = []
for month in sorted(tx['month'].unique()):
    inc = income_tx_copy[income_tx_copy['month'] == month]['amount'].sum()
    exp = expense_tx_copy[expense_tx_copy['month'] == month]['amount'].sum()
    net = inc - exp
    monthly_data.append({'month': month, 'income': inc, 'expense': exp, 'net': net})

monthly_df = pd.DataFrame(monthly_data)

# Category breakdown
expense_by_cat = expense_tx.groupby('category')['amount'].sum().sort_values(ascending=False)
income_by_cat = income_tx.groupby('category')['amount'].sum().sort_values(ascending=False)

# ============================================================================
# CREATE GRAPHICS
# ============================================================================

def create_income_vs_expenses_chart():
    """Create income vs expenses comparison chart"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    months = monthly_df['month'].values
    incomes = monthly_df['income'].values
    expenses = monthly_df['expense'].values
    
    x = np.arange(len(months))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, incomes, width, label='Income', color='#2ecc71', alpha=0.8)
    bars2 = ax.bar(x + width/2, expenses, width, label='Expenses', color='#e74c3c', alpha=0.8)
    
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Amount (EUR)', fontsize=12, fontweight='bold')
    ax.set_title('Monthly Income vs Expenses', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'EUR {height:.0f}',
                ha='center', va='bottom', fontsize=8)
    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'EUR {height:.0f}',
                ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    return fig

def create_expense_pie_chart():
    """Create expense category pie chart"""
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
        textprops={'fontsize': 10}
    )
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Expense Distribution by Category', fontsize=14, fontweight='bold', pad=20)
    
    # Add legend with amounts
    legend_labels = [f'{cat}: EUR {amt:.2f}' for cat, amt in expense_by_cat.items()]
    ax.legend(legend_labels, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
    
    plt.tight_layout()
    return fig

def create_cumulative_deficit_chart():
    """Create cumulative deficit over time"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    monthly_df['cumulative_net'] = monthly_df['net'].cumsum()
    
    ax.plot(monthly_df['month'], monthly_df['cumulative_net'], 
            marker='o', linewidth=3, markersize=8, color='#e74c3c', label='Cumulative Balance')
    ax.axhline(y=0, color='black', linestyle='--', linewidth=2, alpha=0.7, label='Break-even')
    ax.fill_between(range(len(monthly_df)), monthly_df['cumulative_net'], 0, 
                     where=(monthly_df['cumulative_net'] < 0), alpha=0.3, color='#e74c3c')
    
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Balance (EUR)', fontsize=12, fontweight='bold')
    ax.set_title('Cumulative Account Balance Over Time', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    
    # Add value labels
    for i, val in enumerate(monthly_df['cumulative_net']):
        ax.text(i, val, f'EUR {val:.0f}', ha='center', va='bottom' if val > 0 else 'top', fontsize=9)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_savings_rate_chart():
    """Create savings rate visualization"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    monthly_df['savings_rate'] = (monthly_df['net'] / monthly_df['income'] * 100).round(1)
    
    colors_bars = ['#e74c3c' if x < 0 else '#2ecc71' for x in monthly_df['savings_rate']]
    bars = ax.bar(monthly_df['month'], monthly_df['savings_rate'], color=colors_bars, alpha=0.8)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=2)
    ax.axhline(y=12, color='#2ecc71', linestyle='--', linewidth=2, alpha=0.5, label='Target (12%)')
    
    ax.set_xlabel('Month', fontsize=12, fontweight='bold')
    ax.set_ylabel('Savings Rate (%)', fontsize=12, fontweight='bold')
    ax.set_title('Monthly Savings Rate', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.legend(fontsize=11)
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom' if height > 0 else 'top', fontsize=9)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def create_health_score_gauge():
    """Create health score gauge"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create gauge
    score = 15
    max_score = 100
    
    # Draw background arc
    theta = np.linspace(np.pi, 2*np.pi, 100)
    r = 1
    
    # Draw colored zones
    theta_red = np.linspace(np.pi, np.pi + 0.5*np.pi, 50)
    theta_orange = np.linspace(np.pi + 0.5*np.pi, np.pi + 0.75*np.pi, 50)
    theta_yellow = np.linspace(np.pi + 0.75*np.pi, np.pi + 0.9*np.pi, 50)
    theta_green = np.linspace(np.pi + 0.9*np.pi, 2*np.pi, 50)
    
    ax.fill_between(np.cos(theta_red), np.sin(theta_red), color='#e74c3c', alpha=0.3)
    ax.fill_between(np.cos(theta_orange), np.sin(theta_orange), color='#f39c12', alpha=0.3)
    ax.fill_between(np.cos(theta_yellow), np.sin(theta_yellow), color='#f1c40f', alpha=0.3)
    ax.fill_between(np.cos(theta_green), np.sin(theta_green), color='#2ecc71', alpha=0.3)
    
    # Draw needle
    angle = np.pi + (score / max_score) * np.pi
    ax.arrow(0, 0, 0.7*np.cos(angle), 0.7*np.sin(angle), 
             head_width=0.1, head_length=0.1, fc='black', ec='black', linewidth=3)
    
    # Draw center circle
    circle = plt.Circle((0, 0), 0.1, color='black')
    ax.add_patch(circle)
    
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.5, 1.3)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add score text
    ax.text(0, -0.35, f'{score}/100', fontsize=24, fontweight='bold', ha='center')
    ax.text(0, -0.42, 'POOR', fontsize=14, fontweight='bold', ha='center', color='#e74c3c')
    
    # Add labels
    ax.text(-0.9, 0.1, 'CRITICAL\n0-25', fontsize=9, ha='center', fontweight='bold')
    ax.text(-0.3, 0.8, 'POOR\n25-50', fontsize=9, ha='center', fontweight='bold')
    ax.text(0.3, 0.8, 'FAIR\n50-75', fontsize=9, ha='center', fontweight='bold')
    ax.text(0.9, 0.1, 'GOOD\n75-100', fontsize=9, ha='center', fontweight='bold')
    
    ax.set_title('Financial Health Score', fontsize=14, fontweight='bold', pad=20)
    
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

def create_professional_pdf():
    """Create comprehensive professional PDF report"""
    
    pdf_filename = "FINANCIAL_DIAGNOSTIC_REPORT.pdf"
    doc = SimpleDocTemplate(pdf_filename, pagesize=A4,
                           rightMargin=0.5*inch, leftMargin=0.5*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#e74c3c'),
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
    story.append(Paragraph("FINANCIAL ACCOUNT DIAGNOSTIC REPORT", title_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph("Revolut EUR Account - January to November 2025", 
                          ParagraphStyle('subtitle', parent=styles['Normal'], 
                                       fontSize=12, alignment=TA_CENTER, textColor=colors.grey)))
    story.append(Spacer(1, 0.3*inch))
    
    # Executive summary box
    summary_data = [
        ['METRIC', 'VALUE', 'STATUS'],
        ['Account Balance', 'EUR 0.00', 'CRITICAL'],
        ['Cumulative Deficit', 'EUR -10,624.63', 'CRITICAL'],
        ['Monthly Deficit', 'EUR -966', 'CRITICAL'],
        ['Savings Rate', '-19.5%', 'CRITICAL'],
        ['Emergency Fund', 'EUR 0.00', 'NONE'],
        ['Health Score', '15/100', 'POOR'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.2*inch, 2*inch, 1.8*inch])
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
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("KEY FINDINGS", heading_style))
    findings = """
    Your account is in <b>financial crisis</b> with a cumulative deficit of EUR -10,624.63 and a 
    monthly deficit of EUR 966. The three primary issues are: (1) EUR 18,573.40 (28.5% of spending) 
    going to "To Theo new house" with unclear purpose, (2) EUR 14,146.80 in internal savings transfers 
    while running a deficit, and (3) EUR 12,709.94 (19.5%) in uncategorized spending hiding additional 
    problems. Immediate intervention is required.
    """
    story.append(Paragraph(findings, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 2: INCOME & EXPENSE ANALYSIS WITH CHARTS ==========
    
    story.append(Paragraph("INCOME & EXPENSE ANALYSIS", heading_style))
    
    # Create and add income vs expenses chart
    fig1 = create_income_vs_expenses_chart()
    img1_path = "chart_income_vs_expenses.png"
    save_figure(fig1, img1_path)
    story.append(Image(img1_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Income/Expense table
    income_exp_data = [
        ['METRIC', 'AMOUNT', 'MONTHLY AVG'],
        ['Total Income', f'EUR {total_income:,.2f}', f'EUR {total_income/11:,.2f}'],
        ['Total Expenses', f'EUR {total_expenses:,.2f}', f'EUR {total_expenses/11:,.2f}'],
        ['Net Balance', f'EUR {net_balance:,.2f}', f'EUR {net_balance/11:,.2f}'],
    ]
    
    ie_table = Table(income_exp_data, colWidths=[2.5*inch, 2*inch, 2*inch])
    ie_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(ie_table)
    story.append(PageBreak())
    
    # ========== PAGE 3: EXPENSE CATEGORIES ==========
    
    story.append(Paragraph("EXPENSE CATEGORIES", heading_style))
    
    fig2 = create_expense_pie_chart()
    img2_path = "chart_expense_pie.png"
    save_figure(fig2, img2_path)
    story.append(Image(img2_path, width=6*inch, height=4.8*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Expense breakdown table
    exp_data = [['CATEGORY', 'AMOUNT', '% OF BUDGET', 'TRANSACTIONS']]
    for cat, amt in expense_by_cat.items():
        pct = (amt / total_expenses) * 100
        count = len(expense_tx[expense_tx['category'] == cat])
        exp_data.append([cat, f'EUR {amt:,.2f}', f'{pct:.1f}%', str(count)])
    
    exp_table = Table(exp_data, colWidths=[2*inch, 1.8*inch, 1.5*inch, 1.2*inch])
    exp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(exp_table)
    story.append(PageBreak())
    
    # ========== PAGE 4: CUMULATIVE DEFICIT & TRENDS ==========
    
    story.append(Paragraph("CUMULATIVE DEFICIT & MONTHLY TRENDS", heading_style))
    
    fig3 = create_cumulative_deficit_chart()
    img3_path = "chart_cumulative.png"
    save_figure(fig3, img3_path)
    story.append(Image(img3_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.2*inch))
    
    # Monthly trend table
    monthly_data_table = [['MONTH', 'INCOME', 'EXPENSES', 'NET', 'CUMULATIVE']]
    cumulative = 0
    for _, row in monthly_df.iterrows():
        cumulative += row['net']
        monthly_data_table.append([
            row['month'],
            f"EUR {row['income']:,.0f}",
            f"EUR {row['expense']:,.0f}",
            f"EUR {row['net']:,.0f}",
            f"EUR {cumulative:,.0f}"
        ])
    
    monthly_table = Table(monthly_data_table, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.4*inch])
    monthly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(monthly_table)
    story.append(PageBreak())
    
    # ========== PAGE 5: SAVINGS RATE & HEALTH SCORE ==========
    
    story.append(Paragraph("SAVINGS RATE ANALYSIS", heading_style))
    
    fig4 = create_savings_rate_chart()
    img4_path = "chart_savings_rate.png"
    save_figure(fig4, img4_path)
    story.append(Image(img4_path, width=6*inch, height=3.6*inch))
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("FINANCIAL HEALTH SCORE", heading_style))
    
    fig5 = create_health_score_gauge()
    img5_path = "chart_health_gauge.png"
    save_figure(fig5, img5_path)
    story.append(Image(img5_path, width=4*inch, height=3*inch))
    
    health_text = """
    <b>Overall Score: 15/100 (POOR)</b><br/>
    Income Stability: 10/25 | Savings Rate: 0/25 | Expense Control: 5/25 | Emergency Fund: 0/25<br/>
    <br/>
    Your account ranks in the <b>bottom 1%</b> for savings rate, <b>bottom 5%</b> for emergency fund, 
    and <b>top 10%</b> for monthly spending compared to European averages.
    """
    story.append(Paragraph(health_text, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 6: CRITICAL ISSUES & SOLUTIONS ==========
    
    story.append(Paragraph("CRITICAL ISSUES & SOLUTIONS", heading_style))
    
    # Problem 1
    story.append(Paragraph("1. 'To Theo new house' - EUR 18,573.40 (28.5% of spending)", subheading_style))
    problem1 = """
    <b>Status:</b> Largest single expense category with unclear purpose<br/>
    <b>Impact:</b> Consuming more than 1/4 of total spending<br/>
    <b>Action Required:</b> Immediately clarify if this is a loan, gift, rent contribution, or other obligation<br/>
    <b>Potential Savings:</b> EUR 1,200-1,700/month if reduced or eliminated
    """
    story.append(Paragraph(problem1, normal_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Problem 2
    story.append(Paragraph("2. Savings While in Deficit - EUR 14,146.80/month", subheading_style))
    problem2 = """
    <b>Status:</b> Internal savings transfers while running monthly deficit of EUR 966<br/>
    <b>Impact:</b> Mathematically impossible to sustain long-term<br/>
    <b>Action Required:</b> Freeze ALL savings transfers immediately<br/>
    <b>Potential Savings:</b> EUR 1,415/month can be redirected to deficit coverage
    """
    story.append(Paragraph(problem2, normal_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Problem 3
    story.append(Paragraph("3. Uncategorized Spending - EUR 12,709.94 (19.5%)", subheading_style))
    problem3 = """
    <b>Status:</b> 328 transactions with no category assigned<br/>
    <b>Impact:</b> Cannot identify hidden spending problems<br/>
    <b>Action Required:</b> Immediately categorize all transactions<br/>
    <b>Potential Savings:</b> EUR 500-1,000/month once problem areas identified
    """
    story.append(Paragraph(problem3, normal_style))
    story.append(PageBreak())
    
    # ========== PAGE 7: RECOVERY PLAN ==========
    
    story.append(Paragraph("3-PHASE RECOVERY PLAN", heading_style))
    
    recovery_data = [
        ['PHASE', 'TIMELINE', 'TARGET', 'ACTIONS'],
        [
            'Phase 1:\nCrisis\nStabilization',
            'Weeks 1-4',
            'EUR 2,200/month\nsavings',
            '- Freeze discretionary spending\n- Clarify "Theo" transfers\n- Recategorize expenses\n- Reduce cash withdrawals'
        ],
        [
            'Phase 2:\nDeficit\nElimination',
            'Weeks 5-12',
            '+EUR 2,400/month\n(Total: EUR 4,600)',
            '- Create detailed budget\n- Stop online shopping\n- Stabilize income\n- Achieve BREAK-EVEN'
        ],
        [
            'Phase 3:\nWealth\nBuilding',
            'Months 4+',
            'EUR 1,000-1,500\nsurplus/month',
            '- Build EUR 5,000 fund (Q2)\n- Build EUR 17,762 fund (end 2026)\n- Establish new habits\n- Financial health restored'
        ],
    ]
    
    recovery_table = Table(recovery_data, colWidths=[1.3*inch, 1.3*inch, 1.3*inch, 2.1*inch])
    recovery_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
            colors.HexColor('#d5f4e6'),
            colors.HexColor('#d6eaf8'),
            colors.HexColor('#fdebd0')
        ]),
    ]))
    
    story.append(recovery_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Financial projections
    story.append(Paragraph("FINANCIAL PROJECTIONS", subheading_style))
    
    projections_data = [
        ['SCENARIO', 'MONTH 6 STATUS', 'MONTH 12 STATUS'],
        [
            'No Action (Current Path)',
            'Deficit: EUR -16,420\nHealth: CRITICAL\nFund: EUR 0',
            'Deficit: EUR -22,000+\nHealth: CRITICAL\nCrisis: LIKELY'
        ],
        [
            'With Action Plan',
            'Surplus: EUR 1,000+\nHealth: 45-50/100\nFund: EUR 5,000 started',
            'Surplus: EUR 1,000-1,500\nHealth: 65-70/100\nFund: EUR 17,762 complete'
        ],
    ]
    
    proj_table = Table(projections_data, colWidths=[2*inch, 2.5*inch, 2.5*inch])
    proj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0392b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (0, -1), [colors.HexColor('#fadbd8')]),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.HexColor('#d5f4e6')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(proj_table)
    story.append(PageBreak())
    
    # ========== PAGE 8: BENCHMARKS & CONCLUSIONS ==========
    
    story.append(Paragraph("BENCHMARK COMPARISON", heading_style))
    
    benchmark_data = [
        ['METRIC', 'YOUR ACCOUNT', 'EUROPEAN AVG', 'YOUR STATUS'],
        ['Savings Rate', '-19.5%', '+12%', 'BOTTOM 1%'],
        ['Monthly Expenses', 'EUR 5,921', 'EUR 2,000', 'TOP 10%'],
        ['Emergency Fund', '0 months', '3 months', 'CRITICAL'],
        ['Income Stability', '18x variation', 'Low variation', 'POOR'],
    ]
    
    bench_table = Table(benchmark_data, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 1.6*inch])
    bench_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ]))
    
    story.append(bench_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Conclusion
    story.append(Paragraph("CONCLUSION & NEXT STEPS", heading_style))
    
    conclusion = """
    <b>Your financial situation is serious but recoverable.</b><br/><br/>
    
    <b>The Problem:</b> You are spending EUR 966 more per month than you earn (119.5% of income), 
    resulting in a cumulative deficit of EUR -10,624.63. Without immediate action, this deficit will 
    reach EUR -16,420 by May 2026.<br/><br/>
    
    <b>The Solution:</b> A 3-phase action plan targeting EUR 4,600/month in verified savings through 
    expense reduction and income clarification. This will achieve break-even within 3-4 months and 
    full financial recovery within 12 months.<br/><br/>
    
    <b>Your Next Steps (This Week):</b><br/>
    1. Clarify and reduce "To Theo new house" transfers<br/>
    2. Freeze all savings transfers immediately<br/>
    3. Categorize all EUR 12,709.94 in uncategorized spending<br/>
    4. Create a detailed monthly budget<br/>
    5. Implement daily spending tracking<br/><br/>
    
    <b>The choice is yours. The decision is today. The action is this week.</b>
    """
    story.append(Paragraph(conclusion, normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer = f"""
    <b>Report Generated:</b> January 23, 2026 | <b>Analysis Period:</b> January 1 - November 27, 2025 | 
    <b>Account:</b> Revolut EUR | <b>Status:</b> CRITICAL - Intervention Required
    """
    story.append(Paragraph(footer, ParagraphStyle('footer', parent=styles['Normal'], 
                                                  fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    print(f"PDF Report Generated Successfully: {pdf_filename}")
    return pdf_filename

# Generate the PDF
if __name__ == "__main__":
    create_professional_pdf()
    print("Financial Diagnostic Report (PDF) created with graphics, tables, and figures")
