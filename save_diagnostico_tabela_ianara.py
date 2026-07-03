import csv
import json
from pathlib import Path

base = Path("cliente_files/Ianara")
questionario = base / "ianara_apr_2026_diagnostic_input.json"
salario = base / "salary_income_monthly_totals.csv"
out = base / "diagnostico_financeiro_tabela_ianara.csv"

rows = []

if salario.exists():
    with salario.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "periodo": r.get("month", ""),
                    "tipo": "renda_mensal_identificada",
                    "entradas": r.get("monthly_income_total", ""),
                    "saidas": "",
                    "saldo": "",
                    "fonte": "combined_transactions_chronological",
                }
            )

if questionario.exists():
    data = json.loads(questionario.read_text(encoding="utf-8"))
    ds = data.get("diagnostic_summary", {})
    pr = data.get("statement_period", {})
    periodo = f"{pr.get('from', '')} a {pr.get('to', '')}"
    rows.append(
        {
            "periodo": periodo,
            "tipo": "diagnostico_questionario",
            "entradas": ds.get("total_income", ""),
            "saidas": ds.get("total_expenses", ""),
            "saldo": ds.get("estimated_net_cashflow", ""),
            "fonte": "ianara_apr_2026_diagnostic_input.json",
        }
    )

with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["periodo", "tipo", "entradas", "saidas", "saldo", "fonte"],
    )
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out}")
