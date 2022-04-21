"""Unit tests for the `estimator` module."""

import math
from datetime import date

import pytest
from mileage.estimator import (
    Calculator,
    MeanMileage,
    MOTTest,
    ProjectedMileage,
    SaleAdvertisement,
    Vehicle,
    VRMChange,
)


@pytest.fixture(name="vehicle")
def fixture_vehicle() -> Vehicle:
    """Vehicle to be used in tests."""
    return Vehicle(
        vrm="AB51 DVL",
        make="Ford",
        model="Escape Sedan",
        registration_date=date(2001, 9, 1),
    )


def test_add_get_events_no_filter(vehicle: Vehicle) -> None:
    """Verify that timeline events can be added and retrieved from a vehicle."""
    events = vehicle.get_events()
    assert len(events) == 0

    mot_test = MOTTest(date=date(2003, 8, 15), mileage=20_000, result=True)
    vehicle.add_event(mot_test)

    events = vehicle.get_events()
    assert len(events) == 1
    assert events[0] == mot_test


def test_add_get_events_filtered(vehicle: Vehicle) -> None:
    """Verify that timeline events can be added and retrieved from a vehicle.

    A filter is applied.
    """
    vehicle.add_event(MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False))
    vehicle.add_event(MOTTest(date=date(2003, 8, 17), mileage=20_020, result=False))

    events = vehicle.get_events()  # type: ignore
    assert len(events) == 2

    mot_result_filter = lambda event: event.result  # type: ignore
    events = vehicle.get_events(mot_result_filter)  # type: ignore
    assert len(events) == 0

    mot_mileage_filter = lambda event: event.mileage == 20_000  # type: ignore
    events = vehicle.get_events(mot_mileage_filter)  # type: ignore
    assert len(events) == 1


def test_add_get_events_nonchronological(vehicle: Vehicle) -> None:
    """Verify that timeline events are maintained in chronologically ascending order."""
    mot_test = MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False)
    advert = SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    vrm_change = VRMChange(
        date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DVL"
    )

    vehicle.add_event(advert)
    vehicle.add_event(vrm_change)
    vehicle.add_event(mot_test)

    events = vehicle.get_events()
    assert len(events) == 3
    assert isinstance(events[0], MOTTest) and events[0].date == mot_test.date
    assert isinstance(events[1], SaleAdvertisement) and events[1].date == advert.date
    assert isinstance(events[2], VRMChange) and events[2].date == vrm_change.date


def test_add_get_events_duplicate(vehicle: Vehicle) -> None:
    """Verify that the vehicle timeline does not contain duplicate events."""
    vehicle.add_event(MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False))
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )
    vehicle.add_event(
        VRMChange(date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DVL")
    )
    vehicle.add_event(MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False))
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )
    vehicle.add_event(
        VRMChange(date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DVL")
    )

    events = vehicle.get_events()
    assert len(events) == 3
    assert isinstance(events[0], MOTTest)
    assert isinstance(events[1], SaleAdvertisement)
    assert isinstance(events[2], VRMChange)


def test_average_annual_mileage_single_event(vehicle: Vehicle) -> None:
    """Verify calculation of average annual mileage.

    There is a single mileage-present event in the event timeline.
    """
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )

    mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
    assert math.isclose(mean_annual_mileage, 12_008, rel_tol=1e-04)


def test_average_annual_mileage_multi_events(vehicle: Vehicle) -> None:
    """Verify calculation of average annual mileage.

    There are multiple mileage-present events in the event timeline.
    """
    vehicle.add_event(MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False))
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )

    mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
    assert math.isclose(mean_annual_mileage, 12_008, rel_tol=1e-04)


def test_average_annual_mileage_last_no_mileage(vehicle: Vehicle) -> None:
    """Verify calculation of average annual mileage.

    The last timeline event is mileage-absent.
    """
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )
    vehicle.add_event(
        VRMChange(date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DVL")
    )

    mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
    assert math.isclose(mean_annual_mileage, 12_008, rel_tol=1e-04)


def test_average_annual_mileage_no_mileage(vehicle: Vehicle) -> None:
    """Verify calculation of average annual mileage handles no mileage in timeline.

    This can be due to not having events in the timeline or all events in the timeline
    not having mileage information.
    """
    mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
    assert mean_annual_mileage == 7900

    vehicle.add_event(
        VRMChange(date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DCD")
    )
    vehicle.add_event(
        VRMChange(date=date(2003, 11, 10), from_VRM="AB51 DCD", to_VRM="AB51 DVL")
    )

    mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
    assert mean_annual_mileage == 7900


def test_projected_mileage_isolated(vehicle: Vehicle) -> None:
    """Verify projected mileage calculation in using a stubbed average calculator."""

    class StubbedCalculator(Calculator):
        """Stubbed calculator for unit testing."""

        def calculate(self, vehicle: Vehicle) -> float:
            return 15_000

    projected_calculator = ProjectedMileage(StubbedCalculator(), date(2004, 9, 1))
    projected_mileage = vehicle.calculate_timeline(projected_calculator)
    assert math.isclose(projected_mileage, 45_011, rel_tol=1e-04)


def test_projected_mileage_multi_events(vehicle: Vehicle) -> None:
    """Verify projected mileage calculation using a `MeanMileage` calculator.

    The vehicle contains multiple timeline events.
    """
    vehicle.add_event(MOTTest(date=date(2003, 8, 15), mileage=20_000, result=False))
    vehicle.add_event(
        SaleAdvertisement(date=date(2003, 9, 1), mileage=24_000, price=10_000_00)
    )
    vehicle.add_event(
        VRMChange(date=date(2003, 10, 10), from_VRM="AB51 BCD", to_VRM="AB51 DVL")
    )

    projected_calculator = ProjectedMileage(MeanMileage(), date(2004, 9, 1))
    projected_mileage = vehicle.calculate_timeline(projected_calculator)
    assert math.isclose(projected_mileage, 36_032, rel_tol=1e-04)


def test_projected_mileage_no_mileage(vehicle: Vehicle) -> None:
    """Verify projected mileage calculation using a `MeanMileage` calculator.

    The vehicle does not contain timeline events.
    """
    projected_calculator = ProjectedMileage(MeanMileage(), date(2004, 9, 1))
    projected_mileage = vehicle.calculate_timeline(projected_calculator)
    assert math.isclose(projected_mileage, 23_705, rel_tol=1e-04)


def test_event_invalid_date(vehicle: Vehicle) -> None:
    """Verify that adding an event earlier than the registration date is not allowed."""
    with pytest.raises(ValueError):
        vehicle.add_event(MOTTest(date=date(2001, 8, 31), mileage=20_000, result=False))
