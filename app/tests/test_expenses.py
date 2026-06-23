from datetime import datetime
from db import db
from models.Expense import Expense
from models.ExpenseCategory import ExpenseCategory
from repositories.ExpenseRepository import ExpenseRepository
from repositories.SeasonRepository import SeasonRepository


def test_create_expense(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 6)

        expense = Expense(
            price=25.50,
            category=1,
            expenseDate=datetime(2024, 6, 15),
            description="Lunch",
            seasonId=season.id
        )
        expense.save()

        fetched = ExpenseRepository.get_by_id(expense.id)
        assert fetched is not None
        assert fetched.description == "Lunch"


def test_get_expense_by_id(app):
    with app.app_context():
        expense = ExpenseRepository.get_by_id(1)
        assert expense is None or expense.id == 1


def test_get_expenses_by_category(app):
    with app.app_context():
        SeasonRepository.get_or_create(2024, 7)

        expense = Expense(
            price=10.00,
            category=1,
            expenseDate=datetime(2024, 7, 1),
            seasonId=1
        )
        expense.save()

        results = ExpenseRepository.get_by_category(1)
        assert len(results) >= 1
        assert all(e.category == 1 for e in results)


def test_get_expenses_by_season(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 8)

        expense = Expense(
            price=99.99,
            category=1,
            expenseDate=datetime(2024, 8, 10),
            seasonId=season.id
        )
        expense.save()

        results = ExpenseRepository.get_by_season(season.id)
        assert len(results) >= 1
        assert all(e.seasonId == season.id for e in results)


def test_edit_expense(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 9)

        expense = Expense(
            price=50.00,
            category=1,
            expenseDate=datetime(2024, 9, 5),
            description="Original",
            seasonId=season.id
        )
        expense.save()

        expense.edit(price=75.00, description="Updated")
        expense.save()

        fetched = ExpenseRepository.get_by_id(expense.id)
        assert fetched.description == "Updated"


def test_delete_expense(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 10)

        expense = Expense(
            price=15.00,
            category=1,
            expenseDate=datetime(2024, 10, 1),
            seasonId=season.id
        )
        expense.save()
        exp_id = expense.id

        ExpenseRepository.delete_by_id(exp_id)

        assert ExpenseRepository.get_by_id(exp_id) is None


def test_delete_all_expenses(app):
    with app.app_context():
        ExpenseRepository.delete_all()
        remaining = ExpenseRepository.get_by_category(1)
        assert len(remaining) == 0
