# Vehicle Mileage

## History

Code in this repo was originally written for a coding test as part of the interview process with a previous company. The task that was set out is described under the Context section below.

## Context

In order to calculate the valuation of a vehicle, one of the things we need is an estimate of its current mileage. We do this by looking at data points in the vehicle’s history to estimate the vehicle’s average annual mileage. From there we project forward from the most recent event to work out how many miles it will have likely done until now.

We calculate the annual mileage between the data points and then take the average of those.

### Models

#### Vehicle

- id
- VRM (number plate)
- Make (eg Ford)
- Model (eg Fiesta)
- First registration date

The vehicle has a timeline of events that have occurred over the vehicle’s life, such as:

#### Advertised for sale

- date
- price
- mileage

#### MOT test (roadworthy test)

- date
- mileage
- result (pass/fail)

#### Change of VRM (the numberplate changes)

- date
- from VRM
- to VRM

### Task

Provide a way to estimate a vehicle’s current mileage using the timeline

- Calculate the average annual mileage using the events in the timeline
- Estimate the vehicle’s current mileage by projecting from the most recent, event using the
  average annual mileage
- If there are no timeline events with mileage, calculate using 7,900 miles per year as the average

### How to pass the test

- Submit working code. Ideally driven by tests, but command line or web page is fine too.
- You don’t need to build a complete application with a UI or persistence, we’re just interested in seeing how you design and model the domain.
- Don’t use a framework or database. Libraries such as Carbon are fine.
- Following a red-green-refactor TDD process would be great, if you’re familiar with it.

## Notes

### Design

The entire `mileage` module, including docstrings, is less than 200 lines of code. For short scripts, it is typically sufficient to just use functions, written in procedural style. However, I have written it using **classes** (OOD) with focus on extensibility based on the thinking that if it is an actual (large) application, there will be new feature requests to extend its functionality. Hence you will find principles and patterns such as Open-Close Principle and Decorator pattern being employed.

**Type hints** are overkill for short scripts. Similar to the above reasoning, I have chosen to use it as type hints are great for large applications. They can help catch certain errors with the help of IDEs (such as VS Code) and linters (such as mypy), and provide richer documentation in terms of the expected input and output types. Having said that, Python's duck typing is still used as needed, e.g., in `MeanMileage`: `hasattr(event, "mileage")` and where there is a `# type: ignore` comment.

### Implementation

"**Average annual mileage**" is assumed to be mean average, i.e., total mileage / age of vehicle (in years). There can be other averages such as median and mod.

**Calculation of mean annual mileage** is implemented in the `MeanMileage` class and used as follows:

```python
mean_annual_mileage = vehicle.calculate_timeline(MeanMileage())
```

If there is need for calculating the _median_ annual mileage, then a `MedianMileage` class can be implemented, extending from `Calculator`, and used as follows:

```python
median_annual_mileage = vehicle.calculate_timeline(MedianMileage())
```

The **projection of a vehicle's mileage** on a certain date (today or in the future) is implemented by `ProjectedMileage`, which is a decorator of average (mean or median) mileage calculators. It is used as follows:

```python
vehicle.calculate_timeline(ProjectedMileage(MeanMileage(), date(2004, 9, 1)))
```

Similar to the above, mileage projection can be calculated using `ProjectedMileage` based on the vehicle's _median_ annual mileage:

```python
vehicle.calculate_timeline(ProjectedMileage(MedianMileage(), date(2004, 9, 1)))
```

The **default average annual mileage** (i.e., when there are no timeline events with mileage) is implemented by simply setting the default (7,900) in `MeanMileage`'s constructor. If in the future there is need to implement calculation of other averages such as median and mod, the default average annual mileage can be implemented as a decorator to the average calculators, e.g.,

```python
DefaultMileage(MeanMileage())
```

(`DefaultMileage` extends `Calculator`.) This is so that changes to implementation of the default average mileage can be done in one place (Single-Responsibility Principle), in the decorator, be it hardcoded, configurable, or obtained from an external data source. All other implementations of average annual mileage can then use the same default mileage, e.g.,

```python
DefaultMileage(MedianMileage())
```

This can be brought further with mileage projection calculations using various average calculators:

```python
ProjectedMileage(DefaultMileage(MedianMileage()))
```

The current implementation has a **weakness** where it depends of events' properties being named and typed consistently across the timeline events. It is easy to keep them consistent with just a few types of events, but if there are many such event, we would need a programmatic mechanism to ensure properties that represent the same thing (such as `mileage`) are named and typed the same across all events. YAGNI applies for now.

## Instructions

Clone this repo. The rest of the instructions assume you are already in the `vehicle-mileage` directory.

### Viewing the Code

The implementation code is in `src/mileage/estimator.py` and tests in `tests/estimator_tests.py`.

### Basic Requirements

#### Python

I have specified in `setup.py` that Python 3.8 or later is required. I developed it using Python 3.8.10. It may work with Python 3.6 but I have not tested it with versions lower than 3.8.

You may also need to install pip (package installer for Python) if you do not already have it pre-installed on your operating system.

#### Operating System

I developed this on Ubuntu, but I see no reason why it will not work on other operating systems.

The instructions that follow are for Ubuntu and may be slightly different for non-Ubuntu operating systems.

### Installing the Code

Create a Python virtual environment in the `vehicle-mileage` directory and activate it:

```console
$ python3 -m venv venv
$ source venv/bin/activate
```

Install the required Python packages:

```console
$ pip install -r requirements.txt
```

Install the project in "editable" mode:

```console
$ pip install -e .
```

### Running the Tests

The code is driven by tests written using the pytest framework. Run the tests by simply executing the `pytest` command, which you should then see an output similar to the following:

```console
$ pytest -v
================================== test session starts ===================================
platform linux -- Python 3.8.10, pytest-6.2.1, py-1.10.0, pluggy-0.13.1 -- /path_to/vehicle-mileage/venv/bin/python3
cachedir: .pytest_cache
rootdir: /path_to/vehicle-mileage
collected 12 items

tests/estimator_test.py::test_add_get_events_no_filter PASSED                      [  8%]
tests/estimator_test.py::test_add_get_events_filtered PASSED                       [ 16%]
tests/estimator_test.py::test_add_get_events_nonchronological PASSED               [ 25%]
tests/estimator_test.py::test_add_get_events_duplicate PASSED                      [ 33%]
tests/estimator_test.py::test_average_annual_mileage_single_event PASSED           [ 41%]
tests/estimator_test.py::test_average_annual_mileage_multi_events PASSED           [ 50%]
tests/estimator_test.py::test_average_annual_mileage_last_no_mileage PASSED        [ 58%]
tests/estimator_test.py::test_average_annual_mileage_no_mileage PASSED             [ 66%]
tests/estimator_test.py::test_projected_mileage_isolated PASSED                    [ 75%]
tests/estimator_test.py::test_projected_mileage_multi_events PASSED                [ 83%]
tests/estimator_test.py::test_projected_mileage_no_mileage PASSED                  [ 91%]
tests/estimator_test.py::test_event_invalid_date PASSED                            [100%]

=================================== 12 passed in 0.03s ===================================

```

You can also see the tests' code coverage as follows:

```console
$ coverage run --source=src -m pytest
================================== test session starts ===================================
platform linux -- Python 3.8.10, pytest-6.2.1, py-1.10.0, pluggy-0.13.1
rootdir: /path_to/vehicle-mileage
collected 12 items

tests/estimator_test.py ............                                               [100%]

=================================== 12 passed in 0.04s ===================================
$ coverage report
Name                       Stmts   Miss  Cover
----------------------------------------------
src/mileage/__init__.py        0      0   100%
src/mileage/estimator.py      67      0   100%
----------------------------------------------
TOTAL                         67      0   100%
```
