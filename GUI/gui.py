import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sqlite3

import pandas as pd
import numpy as np
import random

DB_PATH = "quant.db"

# Grouped tickers by asset type
ticker_groups = {
    "Stocks": ["MSFT", "NVDA", "META", "GOOGL"],
    "FX Pairs": [
        "EURUSD=X", "GBPUSD=X", "JPY=X", "AUDUSD=X", "CAD=X", "CHF=X", "NZDUSD=X",
        "THB=X", "KRW=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "CHFJPY=X",
        "USDMXN=X", "USDINR=X", "USDZAR=X", "CNH=X"
    ],
    "Equity Indices": [
        "^GSPC", "^DJI", "^IXIC", "^RUT", "^FTSE", "^N225", "^HSI", "^FCHI",
        "^AXJO", "^GDAXI", "^KS11", "^STI"
    ],
    "Commodities": ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "BZ=F"],
    "Bonds & Treasuries": ["ZB=F", "ZN=F", "ZF=F", "^TNX"],
    "Cryptocurrencies": ["BTC-USD", "ETH-USD"]
}

all_tickers = sum(ticker_groups.values(), [])

selected_tickers = []
active_ticker_button = None
custom_builder_selection = []
slider_value = None  # placeholder for the IntVar


def get_strategy_performance(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT strategy, total_return, sharpe_ratio 
        FROM strategy_results 
        WHERE ticker = ?
        ORDER BY sharpe_ratio DESC 
        LIMIT 1;
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_best_strategy_daily_returns(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT strategy FROM strategy_results 
        WHERE ticker = ? 
        ORDER BY sharpe_ratio DESC LIMIT 1
    """
    strat_df = pd.read_sql(query, conn, params=(ticker,))
    if strat_df.empty:
        conn.close()
        return pd.Series(dtype=float)

    strategy = strat_df.iloc[0]["strategy"]
    ret_query = """
        SELECT date, return FROM daily_returns_table 
        WHERE ticker = ? AND strategy = ?
    """
    ret_df = pd.read_sql(ret_query, conn, params=(ticker, strategy))
    conn.close()
    if ret_df.empty:
        return pd.Series(dtype=float)

    ret_df["date"] = pd.to_datetime(ret_df["date"])
    ret_df.set_index("date", inplace=True)
    return ret_df["return"]

def plot_strategy_performance(ticker):
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT strategy, total_return, sharpe_ratio 
        FROM strategy_results 
        WHERE ticker = ?
        ORDER BY sharpe_ratio DESC 
        LIMIT 3;
    """
    df = pd.read_sql(query, conn, params=(ticker,))
    conn.close()

    if df.empty:
        print(f"⚠️ No data found for {ticker}")
        return

    labels, values = zip(*[(s[0], s[1]) for s in df.itertuples(index=False)])
    sharpe_ratios = [s[2] for s in df.itertuples(index=False)]

    for widget in frame_chart.winfo_children():
        widget.destroy()

    # ⬆️ Bigger figure, better font
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#FFA07A", "#FF6347", "#FF4500"]
    bars = ax.barh(labels, values, color=colors, edgecolor='black', linewidth=1.5)
    ax.set_xlabel("Total Return (%)", fontsize=14, color="#003366")
    ax.set_title(f"Top 3 Strategies for {ticker}", fontsize=18, fontweight="bold", color="#003366")

    for bar, sharpe in zip(bars, sharpe_ratios):
        ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height() / 2, f"Sharpe: {sharpe:.2f}", 
                va='center', ha='center', fontsize=14, fontweight='bold', color='white')

    # Center the graph visually on screen
    center_frame = tk.Frame(frame_chart, bg="white")
    center_frame.pack(expand=True, fill="both", padx=30, pady=30)

    canvas = FigureCanvasTkAgg(fig, master=center_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(expand=True)


def show_portfolio_result():
    for widget in frame_chart.winfo_children():
        widget.destroy()

    # Title for Portfolio Result
    tk.Label(frame_chart, text="📊 Selected Portfolio", font=("Arial", 14, "bold")).pack(pady=(10, 10))

    table_frame = tk.Frame(frame_chart)
    table_frame.pack(pady=10)

    headers = ["Ticker", "Best Strategy", "Sharpe Ratio"]
    for col, header in enumerate(headers):
        tk.Label(table_frame, text=header, font=("Arial", 12, "bold"),
                 borderwidth=2, relief="groove", width=18).grid(row=0, column=col)

    all_returns = pd.DataFrame()

    for i, ticker in enumerate(selected_tickers):
        row = get_strategy_performance(ticker)
        if row is not None:
            tk.Label(table_frame, text=ticker, font=("Arial", 11),
                     borderwidth=1, relief="solid", width=18).grid(row=i+1, column=0)
            tk.Label(table_frame, text=row['strategy'], font=("Arial", 11),
                     borderwidth=1, relief="solid", width=18).grid(row=i+1, column=1)
            tk.Label(table_frame, text=f"{row['sharpe_ratio']:.2f}", font=("Arial", 11),
                     borderwidth=1, relief="solid", width=18).grid(row=i+1, column=2)

            daily_returns = get_best_strategy_daily_returns(ticker)
            all_returns[ticker] = daily_returns

    if not all_returns.empty:
        portfolio_returns = all_returns.mean(axis=1)
        total_return = portfolio_returns.sum() * 100
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252) if portfolio_returns.std() != 0 else 0
        cumulative = (1 + portfolio_returns).cumprod()
        peak = cumulative.cummax()
        drawdown = ((peak - cumulative) / peak).max() * 100

        summary_frame = tk.Frame(frame_chart)
        summary_frame.pack(pady=20)

        tk.Label(summary_frame, text="📈 Portfolio Performance Summary",
                 font=("Arial", 14, "bold"), fg="white").grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(summary_frame, text="Total Return:", font=("Arial", 12)).grid(row=1, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{total_return:.2f}%", font=("Arial", 12)).grid(row=1, column=1, sticky='w')
        tk.Label(summary_frame, text="Sharpe Ratio:", font=("Arial", 12)).grid(row=2, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{sharpe:.2f}", font=("Arial", 12)).grid(row=2, column=1, sticky='w')
        tk.Label(summary_frame, text="Max Drawdown:", font=("Arial", 12)).grid(row=3, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{drawdown:.2f}%", font=("Arial", 12)).grid(row=3, column=1, sticky='w')



def open_portfolio_builder():
    for widget in frame_buttons.winfo_children():
        widget.destroy()
    for widget in frame_chart.winfo_children():
        widget.destroy()

    title = tk.Label(frame_buttons, text="Select 5 Instruments", font=("Arial", 14, "bold"))
    title.pack(pady=(0, 10))

    counter_label = tk.Label(frame_buttons, text="0 / 5 Selected", font=("Arial", 12))
    counter_label.pack()

    grid_frame = tk.Frame(frame_buttons)
    grid_frame.pack(pady=10)

    global buttons
    buttons = {}


    def toggle_selection(ticker):
        if ticker in selected_tickers:
            selected_tickers.remove(ticker)
            buttons[ticker].config(bg="white", fg="black")
        elif len(selected_tickers) < 5:
            selected_tickers.append(ticker)
            buttons[ticker].config(bg="white", fg="red")
        counter_label.config(text=f"{len(selected_tickers)} / 5 Selected")


    def reset_selection():
        for t in selected_tickers[:]:
            buttons[t].config(bg="white")
        selected_tickers.clear()
        counter_label.config(text="0 / 5 Selected")

    for i, ticker in enumerate(all_tickers):
        btn = tk.Button(grid_frame, text=ticker, width=12, bg="white", fg="black",
                        command=lambda t=ticker: toggle_selection(t))
        btn.grid(row=i // 5, column=i % 5, padx=5, pady=5)
        buttons[ticker] = btn

    # Create a frame to hold the three buttons in one row
    button_row = tk.Frame(frame_buttons)
    button_row.pack(pady=10)

    # Reset Button
    tk.Button(button_row, text="Reset", command=reset_selection,
            bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)

    # Back Button
    tk.Button(button_row, text="← Back",
        command=lambda: (
            selected_tickers.clear(),
            [w.destroy() for w in frame_chart.winfo_children()],
            show_category_buttons()
        ),
        bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6
    ).pack(side=tk.LEFT, padx=5)

    # Build Portfolio Button
    tk.Button(button_row, text="Build Portfolio", command=show_portfolio_result,
            bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)


def show_tickers_for_group(group_name):
    global active_ticker_button

    for widget in frame_buttons.winfo_children():
        widget.destroy()

    tk.Label(frame_buttons, text=f"{group_name} Tickers", font=("Arial", 14, "bold")).pack(pady=(0,10))

    def on_ticker_click(ticker, button):
        global active_ticker_button
        plot_strategy_performance(ticker)

        if active_ticker_button is not None:
            try:
                active_ticker_button.config(bg="#003366", fg="black")  # Reset previous
            except tk.TclError:
                pass  # Ignore if the widget was destroyed

        button.config(bg="#3399FF", fg="white")  # Highlight current
        active_ticker_button = button


    for ticker in ticker_groups[group_name]:
        btn = tk.Button(frame_buttons, text=ticker,
                        bg="#003366", fg="black", font=("Arial", 11), padx=8, pady=4)
        btn.config(command=lambda t=ticker, b=btn: on_ticker_click(t, b))
        btn.pack(fill='x', padx=5, pady=3)

    tk.Button(frame_buttons, text="← Back",
          command=lambda: (selected_tickers.clear(), show_category_buttons()),
          bg="#AAAAAA", fg="black", font=("Arial", 10)).pack(pady=5)


def show_category_buttons():
    global active_ticker_button
    active_ticker_button = None

    for widget in frame_buttons.winfo_children():
        widget.destroy()

    tk.Label(frame_buttons, text="Select Asset Category", font=("Arial", 14, "bold")).pack(pady=(0,10))

    for group in ticker_groups:
        btn = tk.Button(frame_buttons, text=group,
                        command=lambda g=group: show_tickers_for_group(g),
                        bg="#003366", fg="black", font=("Arial", 12, "bold"),
                        relief="raised", bd=4, padx=10, pady=6)
        btn.pack(fill='x', padx=5, pady=5)

    # 📦 Basic Portfolio button
    tk.Button(frame_buttons, text="📦 Basic Portfolio",
            command=open_portfolio_builder,
            bg="#003366", fg="black", font=("Arial", 12, "bold"),
            relief="raised", bd=4, padx=12, pady=6).pack(fill='x', padx=5, pady=8)

    # ⚙️ Advanced Portfolio button
    tk.Button(frame_buttons, text="⚙️ Advanced Portfolio",
            command=show_custom_builder_screen,
            bg="#003366", fg="black", font=("Arial", 12, "bold"),
            relief="raised", bd=4, padx=12, pady=6).pack(fill='x', padx=5, pady=8)


def show_custom_builder_screen():
    global custom_builder_selection
    custom_builder_selection = []

    for widget in frame_buttons.winfo_children():
        widget.destroy()
    for widget in frame_chart.winfo_children():
        widget.destroy()

    tk.Label(frame_buttons, text="What instruments do you want to trade?", font=("Arial", 14, "bold")).pack(pady=(0, 10))

    grid_frame = tk.Frame(frame_buttons)
    grid_frame.pack()

    category_buttons = {}

    def toggle_category(group, button):
        if group in custom_builder_selection:
            custom_builder_selection.remove(group)
            button.config(bg="#003366", fg="black")
        else:
            custom_builder_selection.append(group)
            button.config(bg="#3399FF", fg="red")
        print("Currently selected:", custom_builder_selection)

    def clear_frames():
        for widget in frame_chart.winfo_children():
            widget.destroy()
        for widget in frame_buttons.winfo_children():
            widget.destroy()


    for i, group in enumerate(ticker_groups):
        btn = tk.Button(grid_frame, text=group,
                        bg="#003366", fg="black", font=("Arial", 12, "bold"),
                        relief="raised", bd=4, padx=10, pady=6)
        btn.config(command=lambda g=group, b=btn: toggle_category(g, b))
        btn.grid(row=i // 2, column=i % 2, padx=10, pady=5)
        category_buttons[group] = btn

    tk.Label(frame_buttons, text="How much money are we putting in?", font=("Arial", 12, "bold"), pady=10).pack()

    global capital_entry
    capital_entry = tk.Entry(frame_buttons, font=("Arial", 12), width=20, justify='center')
    capital_entry.insert(0, "1000000")  # default value
    capital_entry.pack(pady=5)


    button_row = tk.Frame(frame_buttons)
    button_row.pack(pady=15)

    tk.Button(button_row, text="Let's Go!", command=show_custom_ticker_selector,
            bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)

    tk.Button(button_row, text="← Back",
            command=lambda: (clear_frames(), show_category_buttons()),
            bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)



def show_custom_ticker_selector():
    global custom_builder_tickers
    custom_builder_tickers = {}
    category_weight_entries = {}

    for widget in frame_chart.winfo_children():
        widget.destroy()

    right_frame = frame_chart
    tk.Label(right_frame, text="Select Instruments per Category", font=("Arial", 14, "bold")).pack(pady=(10, 10))

    def toggle_ticker(ticker, button, group):
        if ticker in custom_builder_tickers.get(group, []):
            custom_builder_tickers[group].remove(ticker)
            button.config(bg="white", fg="black")
        else:
            custom_builder_tickers.setdefault(group, []).append(ticker)
            button.config(bg="#3399FF", fg="red")
        print("Selected Tickers:", custom_builder_tickers)

    for group in custom_builder_selection:
        # Group label and category weight entry
        row = tk.Frame(right_frame)
        row.pack(pady=(10, 2))
        tk.Label(row, text=f"{group} Weight:", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        entry = tk.Entry(row, width=5)
        entry.insert(0, "0.0")
        entry.pack(side=tk.LEFT, padx=5)
        category_weight_entries[group] = entry

        # Ticker buttons
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack()
        for i, ticker in enumerate(ticker_groups[group]):
            btn = tk.Button(btn_frame, text=ticker, width=10, bg="white",
                            command=lambda t=ticker, g=group, b=None: None)
            btn.grid(row=i // 5, column=i % 5, padx=3, pady=3)
            btn.config(command=lambda t=ticker, g=group, b=btn: toggle_ticker(t, b, g))

    def finalize_portfolio():
        global category_weights
        category_weights = {}
        try:
            cat_total = 0.0
            print("\n📦 Category Weights:")
            for group, entry in category_weight_entries.items():
                val = float(entry.get())
                if not (0 <= val <= 1):
                    raise ValueError(f"Weight for {group} must be between 0 and 1.")
                cat_total += val
                category_weights[group] = val
                print(f"  {group}: {val}")
            print(f"  ➕ Total: {cat_total:.4f}")

            if not (0.9999 <= cat_total <= 1.0002):
                raise ValueError(f"Category weights must sum to approximately 1.0 (currently: {cat_total:.6f})")
            print("✅ All category weights are valid and sum to 1.0")
            show_portfolio_summary()
        except ValueError as e:
            print("❌ Validation Error:", e)


    def auto_build():
        global custom_builder_tickers, category_weights
        custom_builder_tickers = {}
        category_weights = {}

        num_groups = len(custom_builder_selection)
        if num_groups == 0:
            print("❌ Please select at least one category before auto-building.")
            return

        even_weight_raw = 1.0 / num_groups
        even_weight_display = round(even_weight_raw, 4)

        for group in custom_builder_selection:
            tickers = ticker_groups[group]
            chosen = random.sample(tickers, k=min(2, len(tickers)))
            custom_builder_tickers[group] = chosen
            category_weight_entries[group].delete(0, tk.END)
            category_weight_entries[group].insert(0, str(even_weight_display))
            category_weights[group] = even_weight_raw  # Keep full precision

            print(f"Auto-selected for {group}: {chosen}")


        # Highlight buttons that were selected
        for child in right_frame.winfo_children():
            if isinstance(child, tk.Frame):
                for btn in child.winfo_children():
                    if isinstance(btn, tk.Button):
                        ticker = btn["text"]
                        for group, tickers in custom_builder_tickers.items():
                            if ticker in tickers:
                                btn.config(bg="#3399FF", fg="red")

 
    button_row = tk.Frame(right_frame)
    button_row.pack(pady=20)

    tk.Button(button_row, text="✅ Finalize Portfolio",
            command=finalize_portfolio,
            bg="#28A745", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)

    tk.Button(button_row, text="🤖 Build For Me",
            command=auto_build,
            bg="#17A2B8", fg="black", font=("Arial", 12, "bold"), padx=12, pady=6).pack(side=tk.LEFT, padx=5)


def show_portfolio_summary():
    for widget in frame_chart.winfo_children():
        widget.destroy()

    # --- Scrollable Frame Setup ---
    canvas = tk.Canvas(frame_chart, bg="#2e2e2e", highlightthickness=0)
    scroll_y = tk.Scrollbar(frame_chart, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#2e2e2e")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    # Center the scrollable content
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
    def _resize_scrollable(event):
        canvas_width = event.width
        canvas.itemconfig(canvas_window, width=canvas_width)

    canvas.bind("<Configure>", _resize_scrollable)
    canvas.configure(yscrollcommand=scroll_y.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll_y.pack(side="right", fill="y")

    try:
        total_capital = float(capital_entry.get().replace(",", ""))
    except ValueError:
        total_capital = 0

    tk.Label(scrollable_frame, text="💼 Final Portfolio Allocation", font=("Arial", 16, "bold"), bg="#2e2e2e", fg="white").pack(pady=10)

    table = tk.Frame(scrollable_frame, bg="#2e2e2e")
    table.pack(pady=10)

    headers = ["Ticker", "Category", "Allocated Amount ($)", "Best Strategy", "Sharpe Ratio"]
    for col, header in enumerate(headers):
        tk.Label(table, text=header, font=("Arial", 12, "bold"), borderwidth=2, relief="groove", width=22).grid(row=0, column=col)

    all_returns = pd.DataFrame()
    capital_weights = {}
    row_idx = 1

    for group, tickers in custom_builder_tickers.items():
        cat_weight = category_weights.get(group, 0.0)
        per_ticker_amt = (total_capital * cat_weight) / len(tickers) if tickers else 0
        per_ticker_weight = cat_weight / len(tickers) if tickers else 0

        for ticker in tickers:
            row = get_strategy_performance(ticker)
            strategy = row["strategy"] if row is not None else "-"
            sharpe = f"{row['sharpe_ratio']:.2f}" if row is not None else "-"

            tk.Label(table, text=ticker, font=("Arial", 11), borderwidth=1, relief="solid", width=22).grid(row=row_idx, column=0)
            tk.Label(table, text=group, font=("Arial", 11), borderwidth=1, relief="solid", width=22).grid(row=row_idx, column=1)
            tk.Label(table, text=f"${per_ticker_amt:,.2f}", font=("Arial", 11), borderwidth=1, relief="solid", width=22).grid(row=row_idx, column=2)
            tk.Label(table, text=strategy, font=("Arial", 11), borderwidth=1, relief="solid", width=22).grid(row=row_idx, column=3)
            tk.Label(table, text=sharpe, font=("Arial", 11), borderwidth=1, relief="solid", width=22).grid(row=row_idx, column=4)
            row_idx += 1

            capital_weights[ticker] = per_ticker_weight
            daily_returns = get_best_strategy_daily_returns(ticker)
            all_returns[ticker] = daily_returns

    if not all_returns.empty:
        all_returns = all_returns.dropna(how='all')
        weighted_returns = pd.Series(0.0, index=all_returns.index)
        for ticker in all_returns.columns:
            if ticker in capital_weights:
                weighted_returns += all_returns[ticker].fillna(0) * capital_weights[ticker]

        portfolio_returns = weighted_returns
        cumulative = (1 + portfolio_returns).cumprod()
        portfolio_value = cumulative * total_capital

        final_value = portfolio_value.iloc[-1]
        total_profit = final_value - total_capital
        percent_return = (total_profit / total_capital) * 100
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252) if portfolio_returns.std() != 0 else 0
        peak = cumulative.cummax()
        drawdown = ((peak - cumulative) / peak).max() * 100

        # 📊 Summary
        summary_frame = tk.Frame(scrollable_frame, bg="#2e2e2e")
        summary_frame.pack(pady=20)

        tk.Label(summary_frame, text="📊 Portfolio Performance Summary", font=("Arial", 14, "bold"), bg="#2e2e2e", fg="white").grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(summary_frame, text="Total Return (%):", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=1, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{percent_return:.2f}%", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=1, column=1, sticky='w')
        tk.Label(summary_frame, text="Final Portfolio Value:", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=2, column=0, sticky='e')
        tk.Label(summary_frame, text=f"${final_value:,.2f}", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=2, column=1, sticky='w')
        tk.Label(summary_frame, text="Total Profit:", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=3, column=0, sticky='e')
        tk.Label(summary_frame, text=f"${total_profit:,.2f}", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=3, column=1, sticky='w')
        tk.Label(summary_frame, text="Sharpe Ratio:", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=4, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{sharpe:.2f}", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=4, column=1, sticky='w')
        tk.Label(summary_frame, text="Max Drawdown:", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=5, column=0, sticky='e')
        tk.Label(summary_frame, text=f"{drawdown:.2f}%", font=("Arial", 12), bg="#2e2e2e", fg="white").grid(row=5, column=1, sticky='w')

        # 📈 Graph
        fig, ax = plt.subplots(figsize=(7, 4))
        portfolio_value.plot(ax=ax, color="#28A745", linewidth=2)
        ax.set_title("Portfolio Value Over Time", fontsize=13)
        ax.set_ylabel("Value ($)")
        ax.set_xlabel("Year")
        ax.grid(True)

        canvas_plot = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_plot.draw()
        canvas_plot.get_tk_widget().pack(pady=10)




root = tk.Tk()
root.title("Trading Strategy Analyzer")
root.state('zoomed')  # This makes the window fullscreen on Windows
# On macOS/Linux, use: root.attributes('-fullscreen', True)
root.configure(bg="#E6F0FA")


frame_buttons = ttk.Frame(root)
frame_buttons.pack(side=tk.LEFT, fill=tk.BOTH, padx=20, pady=20)

frame_chart = ttk.Frame(root)
frame_chart.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

show_category_buttons()
root.mainloop()
