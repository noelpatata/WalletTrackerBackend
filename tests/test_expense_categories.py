from db import db
from models.ExpenseCategory import ExpenseCategory
from repositories.ExpenseCategoryRepository import ExpenseCategoryRepository
from utils.Constants import ExpenseCategoryMessages


def test_create_category(app):
    with app.app_context():
        category = ExpenseCategory(name="Transport")
        category.save()

        fetched = ExpenseCategoryRepository.get_by_id(category.id)
        assert fetched is not None
        assert fetched.name == "Transport"
        assert fetched.total == 0


def test_get_category_by_id(app):
    with app.app_context():
        assert ExpenseCategoryRepository.get_by_id(1).total == 0


def test_get_all_categories(app):
    with app.app_context():
        all_cats = ExpenseCategoryRepository.get_all()
        assert len(all_cats) >= 1
        names = [c.name for c in all_cats]
        assert "Groceries" in names


def test_edit_category(app):
    with app.app_context():
        cat = ExpenseCategoryRepository.get_by_id(1)
        cat.setName("Food & Groceries")
        cat.save()

        updated = ExpenseCategoryRepository.get_by_id(1)
        assert updated.name == "Food & Groceries"


def test_delete_category(app):
    with app.app_context():
        cat = ExpenseCategory(name="Temp")
        cat.save()
        cat_id = cat.id

        ExpenseCategoryRepository.delete_by_id(cat_id)

        assert ExpenseCategoryRepository.get_by_id(cat_id) is None
