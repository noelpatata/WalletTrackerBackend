from models.Season import Season
from repositories.SeasonRepository import SeasonRepository


def test_create_and_get_season(app):
    with app.app_context():
        season = Season(year=2025, month=1)
        season.save()

        fetched = SeasonRepository.get_by_id(season.id)
        assert fetched is not None
        assert fetched.year == 2025
        assert fetched.month == 1


def test_get_or_create_existing(app):
    with app.app_context():
        first = SeasonRepository.get_or_create(2025, 6)
        second = SeasonRepository.get_or_create(2025, 6)

        assert first.id == second.id


def test_get_or_create_new(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2026, 3)
        assert season is not None
        assert season.year == 2026
        assert season.month == 3


def test_get_all_seasons(app):
    with app.app_context():
        SeasonRepository.get_or_create(2024, 1)
        SeasonRepository.get_or_create(2024, 2)

        all_seasons = SeasonRepository.get_all()
        assert len(all_seasons) >= 2


def test_delete_season(app):
    with app.app_context():
        season = Season(year=2023, month=12)
        season.save()
        sid = season.id

        SeasonRepository.delete_by_id(sid)

        assert SeasonRepository.get_by_id(sid) is None
