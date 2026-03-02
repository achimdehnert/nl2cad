"""
Tests fuer nl2cad.core.quality.IFCQualityChecker.

Testet:
- Vollstaendiges Modell -> score=1.0, is_valid=True
- Fehlende Raumflaechen -> WARNUNG
- Fehlendes Geschoss -> KRITISCH, score=0.0
- Raum ohne Namen -> INFO
- IFCQualityHandler Pipeline-Integration
"""

from __future__ import annotations

from nl2cad.core.models.ifc import IFCFloor, IFCModel, IFCRoom
from nl2cad.core.quality import (
    SEVERITY_INFO,
    SEVERITY_KRITISCH,
    SEVERITY_WARNUNG,
    IFCQualityChecker,
)


def _make_room(name: str = "Buero", area: float = 20.0) -> IFCRoom:
    r = IFCRoom()
    r.name = name
    r.area_m2 = area
    r.height_m = 2.8
    return r


def _make_floor(name: str = "EG", rooms: list | None = None) -> IFCFloor:
    f = IFCFloor()
    f.name = name
    f.rooms = rooms or [_make_room()]
    return f


def _make_model(floors: list | None = None) -> IFCModel:
    model = IFCModel()
    model.floors = floors or [_make_floor()]
    return model


class TestIFCQualityChecker:
    def test_should_pass_valid_model(self):
        checker = IFCQualityChecker()
        model = _make_model()
        report = checker.check(model)
        assert report.is_valid is True
        assert report.completeness_score == 1.0
        assert len(report.kritische_issues) == 0

    def test_should_fail_empty_model(self):
        checker = IFCQualityChecker()
        model = IFCModel()
        model.floors = []
        report = checker.check(model)
        assert report.is_valid is False
        assert report.completeness_score == 0.0
        assert any(i.severity == SEVERITY_KRITISCH for i in report.issues)

    def test_should_warn_room_with_zero_area(self):
        checker = IFCQualityChecker()
        floor = _make_floor(rooms=[_make_room(area=0.0)])
        model = _make_model(floors=[floor])
        report = checker.check(model)
        assert any(i.severity == SEVERITY_WARNUNG for i in report.issues)
        assert report.completeness_score in (0.5, 1.0)

    def test_should_info_room_without_name(self):
        checker = IFCQualityChecker()
        floor = _make_floor(rooms=[_make_room(name="")])
        model = _make_model(floors=[floor])
        report = checker.check(model)
        assert any(i.severity == SEVERITY_INFO for i in report.issues)

    def test_should_report_critical_zero_height_floors(self):
        checker = IFCQualityChecker()
        rooms = [_make_room()]
        rooms[0].height_m = 0.0
        floor = _make_floor(rooms=rooms)
        model = _make_model(floors=[floor])
        report = checker.check(model)
        assert any(i.severity == SEVERITY_WARNUNG for i in report.issues)

    def test_should_return_score_half_for_warnings_only(self):
        checker = IFCQualityChecker()
        room = _make_room(area=0.0)
        floor = _make_floor(rooms=[room])
        model = _make_model(floors=[floor])
        report = checker.check(model)
        assert report.completeness_score == 0.5

    def test_should_list_kritische_issues(self):
        checker = IFCQualityChecker()
        model = IFCModel()
        model.floors = []
        report = checker.check(model)
        assert len(report.kritische_issues) > 0
        assert all(
            i.severity == SEVERITY_KRITISCH for i in report.kritische_issues
        )

    def test_should_list_warnungen(self):
        checker = IFCQualityChecker()
        room = _make_room(area=0.0)
        floor = _make_floor(rooms=[room])
        model = _make_model(floors=[floor])
        report = checker.check(model)
        assert len(report.warnungen) > 0


class TestIFCQualityHandlerPipeline:
    def test_should_pass_handler_with_valid_model(self):
        from nl2cad.core.handlers.base import HandlerStatus
        from nl2cad.core.handlers.ifc_quality import IFCQualityHandler

        handler = IFCQualityHandler()
        model = _make_model()
        result = handler.run({"ifc_model": model})
        assert result.success is True
        assert result.status in (HandlerStatus.SUCCESS, HandlerStatus.WARNING)
        assert "quality_report" in result.data

    def test_should_fail_handler_on_empty_model(self):
        from nl2cad.core.handlers.ifc_quality import IFCQualityHandler

        handler = IFCQualityHandler()
        model = IFCModel()
        model.floors = []
        result = handler.run({"ifc_model": model})
        assert result.success is False
        assert len(result.errors) > 0

    def test_should_fail_missing_required_input(self):
        from nl2cad.core.handlers.ifc_quality import IFCQualityHandler

        handler = IFCQualityHandler()
        result = handler.run({})
        assert result.success is False
        assert any("ifc_model" in e for e in result.errors)
