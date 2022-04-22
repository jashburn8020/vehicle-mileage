"""Vehicle mileage estimator.

Calculate a vehicle's average annual mileage and projected mileage.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Callable, Final, Optional, Tuple
from uuid import uuid4

from sortedcontainers import SortedSet


# The dataclasses (model objects) are frozen - almost immutable.
@dataclass(frozen=True)
class Event:
    """Base event containing common properties."""

    # For simplicity, we're using a naive `date`, i.e., it does not understand
    # timezones. If we need to handle timezones, use `datetime`.
    date: date


@dataclass(frozen=True)
class SaleAdvertisement(Event):
    """An event representing an advertisement for sale."""

    # For simplicity, the price is in pence to avoid errors in floating-point
    # calculations. Its currency is implicit. Proper implementation would involve using
    # a dedicated 'Money' object.
    price: int
    mileage: int


@dataclass(frozen=True)
class MOTTest(Event):
    """An event representing an MOT test."""

    mileage: int
    result: bool


@dataclass(frozen=True)
class VRMChange(Event):
    """An event representing the changing of a vehicle's VRM."""

    from_VRM: str
    to_VRM: str


class Vehicle:
    """A vehicle with an associated event timeline."""

    def __init__(self, vrm: str, make: str, model: str, registration_date: date):
        """Create an instance of a vehicle."""
        self.id = uuid4()
        # For simplicity, we're using a string rather than a VRM format-aware object.
        self.vrm = vrm
        self.make = make
        self.model = model
        self.registration_date = registration_date

        key_func: Callable[[Event], date] = lambda event: event.date
        self._events: SortedSet = SortedSet(key=key_func)

    def add_event(self, event: Event) -> None:
        """Add an event to the vehicle timeline.

        Raises a `ValueError` if the event date is earlier than the vehicle's
        registration date.
        """
        if event.date < self.registration_date:
            raise ValueError(
                f"Event date {event.date} is earlier than the vehicle's registration date"
            )
        self._events.add(event)  # type: ignore

    def get_events(
        self, event_filter: Optional[Callable[[Event], bool]] = None
    ) -> Tuple[Event, ...]:
        """Get events from the vehicle timeline.

        `event_filter` accepts an optional filter function, which if provided, only
        events that match the filter are returned.

        Events that are returned are in chronologically ascending order.
        """
        if event_filter:
            return tuple([event for event in self._events if event_filter(event)])

        return tuple(self._events)

    def calculate_timeline(self, calculator: "Calculator") -> float:
        """Return the result of a calculation against the vehicle timeline events."""
        return calculator.calculate(self)


class Calculator(ABC):
    """Calculator for vehicle timeline events.

    This is the base class for calculators that calculate specific aspects of the
    timeline events.
    """

    DAYS_IN_YEAR: Final[float] = 365.2425

    @abstractmethod
    def calculate(self, vehicle: Vehicle) -> float:
        """Calculate vehicle timeline events."""


class MeanMileage(Calculator):
    """Calculator to calculate average (mean) annual mileage."""

    def __init__(self, default_annual_mileage: int = 7900):
        """Create an instance of the average (mean) annual mileage calculator.

        A default average annual mileage of 7900 is used if it is not specified.
        """
        self.default_annual_mileage = default_annual_mileage

    def calculate(self, vehicle: Vehicle) -> float:
        """Calculate mean annual mileage based on the vehicle's timeline events.

        Returns a default annual mileage if the there are no timeline events, or all
        events in the timeline do not have mileage information.

        This makes use of the most recent timeline event with mileage data. The mean is
        defined as the most recent mileage divided by the number of years between the
        date of the most recent mileage and the date of vehicle registration. It assumes
        that on the day of registration, the vehicle as zero mileage.
        """
        events = vehicle.get_events(lambda event: hasattr(event, "mileage"))
        if not events:
            return self.default_annual_mileage

        # Assumes timeline events are pre-sorted in chronological order.
        last_event = events[-1]

        # Assumes all events in the timeline have dates later than the registration date
        days_to_last_event = (last_event.date - vehicle.registration_date).days
        years_to_last_event = days_to_last_event / Calculator.DAYS_IN_YEAR

        last_event_mileage: int = last_event.mileage  # type: ignore
        mean_annual_mileage = last_event_mileage / years_to_last_event

        return mean_annual_mileage


class ProjectedMileage(Calculator):
    """Calculator to project vehicle's mileage at a certain date.

    This class decorates (wraps) an annual average calculator, which is used to
    calculate the projection.
    """

    def __init__(self, average_calculator: Calculator, projection_date: date):
        """Create an instance of the mileage projection calculator.

        - `average_calculator` is the annual average calculator that will be used in
        the projection calculation.
        - `projection_date` is the date to which to project.
        """
        self._average_calculator = average_calculator
        self._projection_date = projection_date

    def calculate(self, vehicle: Vehicle) -> float:
        """Calculate the projected mileage on the specified date."""
        days_to_projection = (self._projection_date - vehicle.registration_date).days
        years_to_projection = days_to_projection / Calculator.DAYS_IN_YEAR

        annual_average = self._average_calculator.calculate(vehicle)

        return annual_average * years_to_projection
