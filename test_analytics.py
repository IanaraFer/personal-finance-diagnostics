"""Test script to debug analytics issues"""
import pandas as pd
from analytics import analyze_finances
import traceback

try:
    print("Loading data...")
    tx = pd.read_csv('data/transactions_from_pdf.csv')
    acct = pd.read_csv('data/accounts_from_pdf.csv')
    print(f"Loaded {len(tx)} transactions")
    
    print("\nAnalyzing finances...")
    results = analyze_finances(tx, acct)
    
    print("\nSuccess! Results keys:")
    for key in results.keys():
        print(f"  - {key}")
    
    print(f"\nIncome: €{results.get('income', 0):,.2f}")
    print(f"Expenses: €{results.get('expenses', 0):,.2f}")
    
    # Test optimization feature
    if 'optimization' in results:
        opt = results['optimization']
        summary = opt['summary']
        print("\n" + "="*50)
        print("OPTIMIZATION ANALYSIS")
        print("="*50)
        print(f"\nCurrent savings rate: {summary['current_savings_rate']:.1f}%")
        print(f"Potential savings rate: {summary['optimized_savings_rate']:.1f}%")
        print(f"Monthly improvement: +€{summary['total_potential_monthly_savings']:.2f}")
        
    # Test diagnostic report
    if 'diagnostic_report' in results:
        diag = results['diagnostic_report']
        print("\n" + "="*50)
        print("FINANCIAL HEALTH DIAGNOSTIC")
        print("="*50)
        print(f"\nOverall Score: {diag['overall_score']}/100 (Grade: {diag['grade']})")
        print(f"\nCategory Scores:")
        for category, data in diag['diagnostics'].items():
            print(f"  {category:20s}: {data['score']:3d}/100 ({data['status']})")
        
        print(f"\nRisks Identified: {len(diag['risks'])}")
        print(f"Data Gaps: {len(diag['gaps'])}")
        print(f"Recommendations: {len(diag['recommendations'])}")
        print(f"Questionnaire Items: {len(diag['questionnaire'])}")
    
except Exception as e:
    print(f"\nERROR: {str(e)}")
    print("\nFull traceback:")
    print(traceback.format_exc())
