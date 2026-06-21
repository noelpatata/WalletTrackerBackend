from datetime import datetime
from models.Importe import Importe
from models.Season import Season
from repositories.ImporteRepository import ImporteRepository
from repositories.SeasonRepository import SeasonRepository


def test_create_importe(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 1)

        imp = Importe(
            concept="Salary",
            importeDate=datetime(2024, 1, 15),
            amount=3000.00,
            balanceAfter=5000.00,
            seasonId=season.id
        )
        imp.save()

        fetched = ImporteRepository.get_by_id(imp.id)
        assert fetched is not None
        assert fetched.concept == "Salary"
        assert fetched.amount == 3000.00


def test_get_importe_by_id_not_found(app):
    with app.app_context():
        assert ImporteRepository.get_by_id(9999) is None


def test_get_importes_by_season(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 2)

        Importe(
            concept="Freelance",
            importeDate=datetime(2024, 2, 1),
            amount=500.00,
            seasonId=season.id
        ).save()

        results = ImporteRepository.get_by_season_id(season.id)
        assert len(results) >= 1
        assert all(i.seasonId == season.id for i in results)


def test_bulk_create_importes(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 3)

        items = [
            Importe(concept="Job A", importeDate=datetime(2024, 3, 1), amount=100, seasonId=season.id),
            Importe(concept="Job B", importeDate=datetime(2024, 3, 2), amount=200, seasonId=season.id),
        ]
        for item in items:
            item.save()

        results = ImporteRepository.get_by_season_id(season.id)
        concepts = [i.concept for i in results]
        assert "Job A" in concepts
        assert "Job B" in concepts


def test_delete_importe(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 4)

        imp = Importe(
            concept="Temp",
            importeDate=datetime(2024, 4, 1),
            amount=50,
            seasonId=season.id
        )
        imp.save()
        imp_id = imp.id

        ImporteRepository.delete_by_id(imp_id)
        assert ImporteRepository.get_by_id(imp_id) is None


def test_delete_importes_by_season(app):
    with app.app_context():
        season = SeasonRepository.get_or_create(2024, 5)

        Importe(
            concept="Delete me",
            importeDate=datetime(2024, 5, 1),
            amount=10,
            seasonId=season.id
        ).save()

        ImporteRepository.delete_by_season_id(season.id)

        remaining = ImporteRepository.get_by_season_id(season.id)
        assert len(remaining) == 0
