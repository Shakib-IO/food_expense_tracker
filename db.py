# db.py
import sqlite3
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import date

from models import Expense


class AbstractExpenseRepository(ABC):
    """
    Abstract base class for any expense storage backend.
    """

    @abstractmethod
    def add(self, expense: Expense) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_all(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        day: Optional[int] = None,
    ) -> List[Expense]:
        """
        Return all expenses, optionally filtered by month/year/day.
        """
        raise NotImplementedError

    @abstractmethod
    def get_totals(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        day: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Return total amounts per spender for the given period.
        """
        raise NotImplementedError


class SQLiteExpenseRepository(AbstractExpenseRepository):
    """
    Concrete implementation of AbstractExpenseRepository using SQLite.

    Uses a single 'expenses' table, but it’s indexed on date so
    filtering by month/year/day scales well as data grows.
    """

    def __init__(self, db_path: str = "expenses.db") -> None:
        self.db_path = db_path
        self._create_table()
        self._create_indexes()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _create_table(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spender TEXT NOT NULL,
                    date TEXT NOT NULL,  -- ISO: YYYY-MM-DD
                    shop TEXT NOT NULL,
                    amount REAL NOT NULL
                )
                """
            )
            conn.commit()

    def _create_indexes(self) -> None:
        """
        Index on date and spender to scale lookups as data grows.
        """
        with self._get_connection() as conn:
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_expenses_spender ON expenses(spender)"
            )
            conn.commit()

    def add(self, expense: Expense) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO expenses (spender, date, shop, amount)
                VALUES (?, ?, ?, ?)
                """,
                (expense.spender, expense.date.isoformat(), expense.shop, expense.amount),
            )
            conn.commit()

    def _build_where_clause(
        self,
        month: Optional[int],
        year: Optional[int],
        day: Optional[int],
    ):
        conditions = []
        params: List[str] = []

        if year is not None:
            conditions.append("strftime('%Y', date) = ?")
            params.append(str(year))

        if month is not None:
            conditions.append("strftime('%m', date) = ?")
            params.append(f"{month:02d}")

        if day is not None:
            conditions.append("strftime('%d', date) = ?")
            params.append(f"{day:02d}")

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        return where_clause, params

    def list_all(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        day: Optional[int] = None,
    ) -> List[Expense]:
        base_query = """
            SELECT id, spender, date, shop, amount
            FROM expenses
        """

        where_clause, params = self._build_where_clause(month, year, day)
        query = base_query + where_clause + " ORDER BY date ASC, id DESC"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        expenses: List[Expense] = []
        for row_id, spender, date_str, shop, amount in rows:
            expenses.append(
                Expense(
                    id=row_id,
                    spender=spender,
                    date=date.fromisoformat(date_str),
                    shop=shop,
                    amount=amount,
                )
            )
        return expenses

    def get_totals(
        self,
        month: Optional[int] = None,
        year: Optional[int] = None,
        day: Optional[int] = None,
    ) -> Dict[str, float]:
        base_query = """
            SELECT spender, SUM(amount)
            FROM expenses
        """

        where_clause, params = self._build_where_clause(month, year, day)
        query = base_query + where_clause + " GROUP BY spender"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return {spender: (total or 0.0) for spender, total in rows}
