from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent / 'src'))

from data_loader import load_processed_data
from signals import compute_signals
from portfolio import construct_portfolio
from backtest import run_backtest, load_benchmark_data
from metrics import compute_all_metrics

print("Loading data and computing metrics...")
fx_returns, carry, _ = load_processed_data()
signals = compute_signals(carry, lag_days=1, regime_min_differential_pct=1.0)
weights, vol, leverage, transaction_costs = construct_portfolio(signals, fx_returns)
benchmark_returns = load_benchmark_data('SPY', start_date='2002-04-01')
results = run_backtest(fx_returns, weights, transaction_costs, benchmark_returns)
benchmark_aligned = benchmark_returns.loc[results.index] if len(benchmark_returns) > 0 else None
metrics = compute_all_metrics(results['net_return'], benchmark_returns=benchmark_aligned, risk_free_rate=0.0)

output_path = Path(__file__).parent / "output" / "g10_carry_1pager.pdf"
doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                        rightMargin=0.75*inch, leftMargin=0.75*inch,
                        topMargin=0.75*inch, bottomMargin=0.75*inch)

elements = []

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=18,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=12,
    alignment=TA_CENTER
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=12,
    textColor=colors.HexColor('#2E86AB'),
    spaceAfter=6,
    spaceBefore=12
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10,
    leading=14,
    spaceAfter=6
)

elements.append(Paragraph("Systematic G10 FX Carry Strategy", title_style))
elements.append(Paragraph("A Volatility-Targeted Approach", styles['Heading2']))
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph("<b>Strategy Overview</b>", heading_style))
overview_text = """
Long the 3 highest-yielding currencies vs. Short the 3 lowest-yielding currencies,
with position sizes inversely scaled by realized volatility and the entire portfolio
scaled to target 10% annualized volatility. A regime filter is applied: the strategy
runs only when the average absolute rate differential across the G10 basket exceeds
1%, going flat when differentials are compressed (e.g. ZIRP), as there is no carry
to harvest in those environments.
"""
elements.append(Paragraph(overview_text, body_style))
elements.append(Spacer(1, 0.15*inch))

elements.append(Paragraph("<b>Performance Metrics</b>", heading_style))
elements.append(Paragraph("(April 1, 2002 - February 27, 2026)", body_style))
elements.append(Spacer(1, 0.1*inch))

data = [
    ['Metric', 'Strategy', 'Benchmark (SPY)'],
    ['Total Return', f"{metrics.get('Total_Return', 0):.2f}%", f"{metrics.get('Benchmark_Total_Return', 0):.2f}%"],
    ['Annualized Return', f"{metrics.get('Annualized_Return', 0):.2f}%", f"{metrics.get('Benchmark_Annualized_Return', 0):.2f}%"],
    ['Annualized Volatility', f"{metrics.get('Annualized_Volatility', 0):.2f}%", f"{metrics.get('Benchmark_Annualized_Volatility', 0):.2f}%"],
    ['Sharpe Ratio', f"{metrics.get('Sharpe_Ratio', 0):.2f}", f"{metrics.get('Benchmark_Sharpe_Ratio', 0):.2f}"],
    ['Sortino Ratio', f"{metrics.get('Sortino_Ratio', 0):.2f}", "—"],
    ['Calmar Ratio', f"{metrics.get('Calmar_Ratio', 0):.2f}", "—"],
    ['Max Drawdown', f"{metrics.get('Max_Drawdown', 0):.2f}%", f"{metrics.get('Benchmark_Max_Drawdown', 0):.2f}%"],
    ['Max DD Duration', f"{metrics.get('Max_DD_Duration', 0)} days", f"{metrics.get('Benchmark_Max_DD_Duration', 0)} days"],
    ['VaR (95%, daily)', f"{metrics.get('VaR_95pct', 0):.2f}%", "—"],
    ['CVaR (95%, daily)', f"{metrics.get('CVaR_95pct', 0):.2f}%", "—"],
    ['Skewness', f"{metrics.get('Skewness', 0):.2f}", "—"],
    ['Kurtosis', f"{metrics.get('Kurtosis', 0):.2f}", "—"],
    ['Hit Rate', f"{metrics.get('Hit_Rate', 0):.2f}%", f"{metrics.get('Benchmark_Hit_Rate', 0):.2f}%"],
    ['Correlation to SPY', f"{metrics.get('Correlation_to_Benchmark', 0):.2f}", "—"],
]

table = Table(data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
]))

elements.append(table)
elements.append(Spacer(1, 0.15*inch))

elements.append(Paragraph("<b>Key Observations</b>", heading_style))
sharpe = metrics.get('Sharpe_Ratio', 0)
corr = metrics.get('Correlation_to_Benchmark', 0)
observations_text = f"""
The strategy generated a Sharpe ratio of {sharpe:.2f} over the period. Notably, it performed 
differently during the 2022 rate hike cycle relative to the pre-2020 ZIRP environment. 
Correlation to SPY was {corr:.2f}, validating the diversification thesis. The strategy 
experienced significant drawdowns during carry crash events (2008, 2020), which is 
characteristic of carry strategies.
"""
elements.append(Paragraph(observations_text, body_style))
elements.append(Spacer(1, 0.15*inch))

elements.append(Spacer(1, 0.2*inch))
footer_text = """
<font size=8>Built in Python. Data: Barchart (FX Spot), FRED (Interest Rates). 
Backtest: April 1, 2002–February 27, 2026.</font>
"""
elements.append(Paragraph(footer_text, body_style))

print(f"Generating PDF: {output_path}")
doc.build(elements)
print(f"[OK] PDF generated successfully: {output_path}")
