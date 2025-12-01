from datetime import date, datetime
from calendar import month_name

from flask import Flask, render_template, request, redirect, url_for

from db import SQLiteExpenseRepository
from models import Expense
from compute import compute_balance_message


app = Flask(__name__)

# Predefined shop names
SHOP_CHOICES = [
    "Mizan",
    "Newon",
    "Madina",
    "Beau-Soir",
    "Costco",
    "Restaurents",
    "Walmart",
    "Amazon"
]

# Month choices for dropdown: (1, "January"), (2, "February"), ...
MONTH_CHOICES = [(i, month_name[i]) for i in range(1, 13)]

# Simple year choices (you can adjust this range as you like)
CURRENT_YEAR = datetime.now().year
YEAR_CHOICES = list(range(CURRENT_YEAR - 2, CURRENT_YEAR + 3))

# Our repository instance
repo = SQLiteExpenseRepository("expenses.db")


@app.route("/", methods=["GET"])
def index():
    # Read month/year filters from query parameters (?month=5&year=2025)
    month_str = request.args.get("month", "").strip()
    year_str = request.args.get("year", "").strip()

    month = int(month_str) if month_str.isdigit() else None
    year = int(year_str) if year_str.isdigit() else None

    # Get filtered expenses and totals
    expenses = repo.list_all(month=month, year=year)
    totals = repo.get_totals(month=month, year=year)

    balance_message = compute_balance_message(totals)

    return render_template(
        "home.html",
        expenses=expenses,
        totals=totals,
        shops=SHOP_CHOICES,
        months=MONTH_CHOICES,
        years=YEAR_CHOICES,
        selected_month=month,
        selected_year=year,
        balance_message=balance_message,
    )

@app.route("/")
def home():
    """
    Home page: user selects View or Update.
    """
    return render_template("home.html")


@app.route("/view", methods=["GET"])
def view_expenses():
    month_str = request.args.get("month", "").strip()
    year_str = request.args.get("year", "").strip()
    day_str = request.args.get("day", "").strip()

    month = int(month_str) if month_str.isdigit() else None
    year = int(year_str) if year_str.isdigit() else None
    day = int(day_str) if day_str.isdigit() else None

    show_results = month is not None  # 🔴 only show results if month is chosen

    if show_results:
        expenses = repo.list_all(month=month, year=year, day=day)
        totals = repo.get_totals(month=month, year=year, day=day)
        balance_message = compute_balance_message(totals)
    else:
        expenses = []
        totals = {}
        balance_message = "Please select a month to see expenses."

    return render_template(
        "view.html",
        expenses=expenses,
        totals=totals,
        months=MONTH_CHOICES,
        years=YEAR_CHOICES,
        selected_month=month,
        selected_year=year,
        selected_day=day,
        balance_message=balance_message,
        show_results=show_results,   # 👈 pass this flag to template
    )


@app.route("/update", methods=["GET", "POST"])
def update_expense():
    """
    Page to add (update) expenses.
    """
    if request.method == "POST":
        spender = request.form["spender"]   # "Shakib" or "Junit"
        date_str = request.form["date"]     # "YYYY-MM-DD"
        shop = request.form["shop"]
        amount_str = request.form["amount"]

        amount = float(amount_str) if amount_str else 0.0
        expense_date = date.fromisoformat(date_str)

        new_expense = Expense(
            id=None,
            spender=spender,
            date=expense_date,
            shop=shop,
            amount=amount,
        )

        repo.add(new_expense)

        # After update, redirect back to home or view
        return redirect(url_for("home"))

    # GET: show the form
    return render_template(
        "update.html",
        shops=SHOP_CHOICES,
    )


if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on your network to access your laptop (optional)
    app.run(debug=True, host="0.0.0.0", port=8000)