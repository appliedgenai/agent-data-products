#!/usr/bin/env python3
"""Synthetic arithmetic and contract demonstration for paper section 3.

Run with Python 3.10+; only the standard library is used.

The fixtures represent FROZEN CERTIFIED INPUT, not a certification system.
Each month's input is assumed complete as of the next month's opening boundary
plus seven days. The order-level full-delivery timestamp is assumed to have
been certified upstream. Shipments illustrate an incorrect join; they do not
establish shipment completeness or derive the full-delivery timestamp.

This example does not test bitemporal ingestion, knowledge-at-cutoff queries,
replay state, late-correction/restatement workflows, authentication, permissions,
or an enterprise implementation. Destination timezones use a synthetic fixed
UTC-05:00 offset: local-month/UTC comparison is tested, but DST and historical
timezone changes are not. Region and hierarchy assignments are supplied facts.
"""

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
import sys
import unittest


UTC = timezone.utc
DESTINATION_ZONE = timezone(timedelta(hours=-5), "Synthetic UTC-05:00")
REGIONS = ("North", "South")
METRIC_VERSION = 1


class ContractError(ValueError):
    """The supplied input cannot support this metric contract."""


@dataclass(frozen=True)
class Cohort:
    as_of: date
    strategic_parents: frozenset[str]
    customer_parent: tuple[tuple[str, str], ...]

    def includes(self, customer_id: str) -> bool:
        hierarchy = dict(self.customer_parent)
        if customer_id not in hierarchy:
            raise ContractError(f"Unresolved customer hierarchy: {customer_id}")
        return hierarchy[customer_id] in self.strategic_parents


COHORT = Cohort(
    as_of=date(2026, 7, 1),
    strategic_parents=frozenset({"strategic-north", "strategic-south"}),
    customer_parent=(
        ("customer-north", "strategic-north"),
        ("customer-south", "strategic-south"),
        ("customer-new", "non-strategic"),
    ),
)


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_id: str
    production: bool
    first_deadline_utc: datetime | None
    destination_zone: timezone
    region_at_commit: str | None
    fully_delivered_utc: datetime | None
    canceled_utc: datetime | None = None
    revised_deadline_utc: datetime | None = None


@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    order_id: str


@dataclass(frozen=True)
class FrozenInput:
    period: str
    snapshot_id: str
    frozen_at_utc: datetime
    orders: tuple[Order, ...]
    shipments: tuple[Shipment, ...]


@dataclass(frozen=True)
class Counts:
    on_time: int
    due: int

    @property
    def rate(self) -> Fraction | None:
        return Fraction(self.on_time, self.due) if self.due else None


def freeze_time(period: str) -> datetime:
    year, month = map(int, period.split("-"))
    next_month = datetime(
        year + (month == 12), month % 12 + 1, 1, tzinfo=DESTINATION_ZONE
    )
    return (next_month + timedelta(days=7)).astimezone(UTC)


def utc_instant(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ContractError(f"{name} must be an aware UTC instant")


def eligible_orders(snapshot: FrozenInput, cohort: Cohort = COHORT) -> tuple[Order, ...]:
    """Validate input and select eligible orders without joining shipments."""
    if snapshot.frozen_at_utc != freeze_time(snapshot.period):
        raise ContractError("Input does not carry the expected monthly freeze time")
    ids = [order.order_id for order in snapshot.orders]
    if len(ids) != len(set(ids)):
        raise ContractError("Duplicate order IDs block the calculation")
    if len(dict(cohort.customer_parent)) != len(cohort.customer_parent):
        raise ContractError("Customer hierarchy must have one parent per customer")

    eligible = []
    for order in snapshot.orders:
        if not order.production or not cohort.includes(order.customer_id):
            continue
        if order.first_deadline_utc is None:
            raise ContractError(f"Missing first committed deadline: {order.order_id}")
        utc_instant(order.first_deadline_utc, "First deadline")
        if order.destination_zone != DESTINATION_ZONE:
            raise ContractError("This fixture supports only its stated fixed timezone")
        month = order.first_deadline_utc.astimezone(order.destination_zone).strftime("%Y-%m")
        if month != snapshot.period:
            continue
        for name, instant in (
            ("Full delivery", order.fully_delivered_utc),
            ("Cancellation", order.canceled_utc),
        ):
            if instant is not None:
                utc_instant(instant, name)
                if instant > snapshot.frozen_at_utc:
                    raise ContractError(f"{name} lies beyond the frozen input cutoff")
        if order.canceled_utc is not None and order.canceled_utc < order.first_deadline_utc:
            continue
        if order.region_at_commit not in REGIONS:
            raise ContractError(f"Unresolved commitment region: {order.order_id}")
        eligible.append(order)
    return tuple(eligible)


def on_time(order: Order) -> bool:
    # Only validated eligible orders reach this function. A revised promise is
    # intentionally not an input to the approved comparison.
    return order.fully_delivered_utc is not None and order.fully_delivered_utc <= order.first_deadline_utc


def count(orders: tuple[Order, ...]) -> Counts:
    return Counts(sum(on_time(order) for order in orders), len(orders))


def report(snapshot: FrozenInput, cohort: Cohort = COHORT) -> dict[str, Counts]:
    if cohort != COHORT:
        raise ContractError("Metric v1 requires the fixed July 1 cohort and hierarchy snapshot")
    orders = eligible_orders(snapshot, cohort)
    result = {
        region: count(tuple(order for order in orders if order.region_at_commit == region))
        for region in REGIONS
    }
    result["Total"] = count(orders)
    return result


def fixed_mix_rate(reference: dict[str, Counts], target: dict[str, Counts]) -> Fraction | None:
    """Use reference-period due-order shares and target-period regional rates."""
    total = reference["Total"].due
    if not total:
        return None
    weighted = Fraction(0)
    for region in REGIONS:
        if reference[region].due:
            if target[region].rate is None:
                return None
            weighted += Fraction(reference[region].due, total) * target[region].rate
    return weighted


def wrong_shipment_join(snapshot: FrozenInput) -> Counts:
    """Deliberately wrong: a left join weights orders by shipment multiplicity."""
    multiplicity = Counter(shipment.order_id for shipment in snapshot.shipments)
    joined = tuple(
        order
        for order in eligible_orders(snapshot)
        for _ in range(max(1, multiplicity[order.order_id]))
    )
    return count(joined)


def make_fixture(period: str, north: tuple[int, int], south: tuple[int, int]) -> FrozenInput:
    """Build counts independently specified as (on time, due), plus distractors."""
    year, month = map(int, period.split("-"))
    deadline = datetime(year, month, 15, 17, tzinfo=DESTINATION_ZONE).astimezone(UTC)
    orders = []
    for region, (timely, total) in (("North", north), ("South", south)):
        for number in range(1, total + 1):
            delivery = deadline - timedelta(hours=1) if number <= timely else deadline + timedelta(hours=2)
            if number == total:
                delivery = None  # Still undelivered at the frozen cutoff.
            orders.append(Order(
                order_id=f"{period}-{region}-{number:03}",
                customer_id=f"customer-{region.lower()}",
                production=True,
                first_deadline_utc=deadline,
                destination_zone=DESTINATION_ZONE,
                region_at_commit=region,
                fully_delivered_utc=delivery,
                canceled_utc=deadline + timedelta(seconds=1) if region == "South" and number == total else None,
                revised_deadline_utc=deadline + timedelta(days=1) if region == "North" and number == timely + 1 else None,
            ))
    base = orders[0]
    orders.extend((
        replace(base, order_id=f"{period}-noncohort", customer_id="customer-new"),
        replace(base, order_id=f"{period}-test-order", production=False),
        replace(base, order_id=f"{period}-prior-cancel", canceled_utc=deadline - timedelta(seconds=1), fully_delivered_utc=None),
        replace(base, order_id=f"{period}-other-month", first_deadline_utc=deadline - timedelta(days=31), fully_delivered_utc=None),
    ))
    shipments = [Shipment(f"shipment-{order.order_id}", order.order_id) for order in orders if order.fully_delivered_utc]
    # Add a shipment to a late July order and an on-time August order.
    fanout_id = f"{period}-North-{north[0] + 1:03}" if period == "2026-07" else f"{period}-South-001"
    shipments.append(Shipment(f"extra-shipment-{period}", fanout_id))
    return FrozenInput(period, f"synthetic-frozen-certified-{period}-v1", freeze_time(period), tuple(orders), tuple(shipments))


JULY = make_fixture("2026-07", (76, 80), (14, 20))
AUGUST = make_fixture("2026-08", (38, 40), (42, 60))


class ContractTests(unittest.TestCase):
    def test_published_counts_and_reconciliation(self):
        for snapshot, north, south, total in (
            (JULY, Counts(76, 80), Counts(14, 20), Counts(90, 100)),
            (AUGUST, Counts(38, 40), Counts(42, 60), Counts(80, 100)),
        ):
            result = report(snapshot)
            self.assertEqual(result, {"North": north, "South": south, "Total": total})
            self.assertEqual(sum(result[r].due for r in REGIONS), total.due)
            self.assertEqual(sum(result[r].on_time for r in REGIONS), total.on_time)

    def test_rates_and_fixed_july_mix(self):
        july, august = report(JULY), report(AUGUST)
        self.assertEqual(july["Total"].rate, Fraction(9, 10))
        self.assertEqual(august["Total"].rate, Fraction(4, 5))
        self.assertEqual(august["Total"].rate - july["Total"].rate, Fraction(-1, 10))
        for result in (july, august):
            self.assertEqual(result["North"].rate, Fraction(19, 20))
            self.assertEqual(result["South"].rate, Fraction(7, 10))
        self.assertEqual(fixed_mix_rate(july, august), Fraction(9, 10))

    def test_zero_denominator_is_unavailable(self):
        empty = report(replace(JULY, orders=(), shipments=()))
        self.assertIsNone(empty["Total"].rate)
        self.assertIsNone(fixed_mix_rate(empty, report(AUGUST)))
        self.assertIsNone(fixed_mix_rate(report(JULY), empty))

    def test_undelivered_orders_remain_due(self):
        eligible = eligible_orders(JULY)
        self.assertEqual(sum(order.fully_delivered_utc is None for order in eligible), 2)
        delivered_only = tuple(order for order in eligible if order.fully_delivered_utc is not None)
        self.assertEqual(count(delivered_only), Counts(90, 98))
        self.assertNotEqual(count(delivered_only).rate, count(eligible).rate)

    def test_cancellation_before_at_and_after_deadline(self):
        base = replace(JULY.orders[0], fully_delivered_utc=None)
        for offset, expected_due in ((-1, 0), (0, 1), (1, 1)):
            order = replace(base, canceled_utc=base.first_deadline_utc + timedelta(seconds=offset))
            self.assertEqual(report(replace(JULY, orders=(order,)))["Total"], Counts(0, expected_due))

    def test_revised_promise_cannot_hide_lateness(self):
        late = next(order for order in JULY.orders if order.revised_deadline_utc is not None)
        self.assertLessEqual(late.fully_delivered_utc, late.revised_deadline_utc)
        self.assertGreater(late.fully_delivered_utc, late.first_deadline_utc)
        self.assertEqual(report(replace(JULY, orders=(late,)))["Total"], Counts(0, 1))

    def test_delivery_exactly_at_deadline_is_on_time(self):
        order = replace(JULY.orders[0], fully_delivered_utc=JULY.orders[0].first_deadline_utc)
        self.assertEqual(report(replace(JULY, orders=(order,)))["Total"], Counts(1, 1))

    def test_fixed_cohort_and_hierarchy_exclude_new_members(self):
        self.assertEqual(COHORT.as_of, date(2026, 7, 1))
        august_ids = {order.customer_id for order in eligible_orders(AUGUST)}
        self.assertEqual(august_ids, {"customer-north", "customer-south"})
        # An illustrative later hierarchy would move South out and a new
        # customer in. The selection helper exposes the wrong population;
        # the v1 reporting interface rejects that substitute snapshot.
        later = replace(COHORT, as_of=date(2026, 8, 1), customer_parent=(
            ("customer-north", "strategic-north"),
            ("customer-south", "non-strategic"),
            ("customer-new", "strategic-south"),
        ))
        self.assertEqual(count(eligible_orders(AUGUST, later)), Counts(39, 41))
        with self.assertRaisesRegex(ContractError, "fixed July 1"):
            report(AUGUST, later)
        self.assertEqual(report(AUGUST)["Total"], Counts(80, 100))

    def test_production_cancellation_and_period_filters(self):
        ids = {order.order_id for order in eligible_orders(JULY)}
        self.assertEqual(len(JULY.orders), 104)
        self.assertEqual(len(ids), 100)
        for suffix in ("noncohort", "test-order", "prior-cancel", "other-month"):
            self.assertNotIn(f"2026-07-{suffix}", ids)

    def test_region_is_commitment_assignment(self):
        # Region comes from the order's commitment fact, not the customer's
        # name or parent. A cross-region commitment groups in its assigned region.
        order = replace(JULY.orders[0], region_at_commit="South")
        result = report(replace(JULY, orders=(order,)))
        self.assertEqual(result["North"], Counts(0, 0))
        self.assertEqual(result["South"], Counts(1, 1))

    def test_duplicate_orders_reject(self):
        with self.assertRaisesRegex(ContractError, "Duplicate"):
            report(replace(JULY, orders=JULY.orders + (JULY.orders[0],)))

    def test_missing_deadline_and_invalid_region_reject(self):
        for fields in ({"first_deadline_utc": None}, {"region_at_commit": None}, {"region_at_commit": "Unknown"}):
            with self.subTest(fields=fields), self.assertRaises(ContractError):
                report(replace(JULY, orders=(replace(JULY.orders[0], **fields),)))

    def test_missing_or_duplicate_hierarchy_reject(self):
        for cohort in (replace(COHORT, customer_parent=()), replace(COHORT, customer_parent=COHORT.customer_parent + (COHORT.customer_parent[0],))):
            with self.assertRaises(ContractError):
                eligible_orders(JULY, cohort)

    def test_freeze_boundary_label_and_mismatched_cutoff(self):
        self.assertEqual(JULY.frozen_at_utc, datetime(2026, 8, 8, 5, tzinfo=UTC))
        self.assertEqual(AUGUST.frozen_at_utc, datetime(2026, 9, 8, 5, tzinfo=UTC))
        with self.assertRaisesRegex(ContractError, "freeze time"):
            report(replace(JULY, frozen_at_utc=JULY.frozen_at_utc - timedelta(days=1)))

    def test_local_deadline_month_uses_original_timezone(self):
        deadline = datetime(2026, 8, 1, 4, 30, tzinfo=UTC)  # July 31, 23:30 locally.
        order = replace(JULY.orders[0], first_deadline_utc=deadline, fully_delivered_utc=deadline)
        self.assertEqual(report(replace(JULY, orders=(order,)))["Total"], Counts(1, 1))
        self.assertEqual(report(replace(AUGUST, orders=(order,)))["Total"], Counts(0, 0))

    def test_non_utc_or_post_cutoff_facts_reject(self):
        for fields in (
            {"first_deadline_utc": datetime(2026, 7, 15)},
            {"fully_delivered_utc": JULY.frozen_at_utc + timedelta(seconds=1)},
        ):
            with self.subTest(fields=fields), self.assertRaises(ContractError):
                report(replace(JULY, orders=(replace(JULY.orders[0], **fields),)))

    def test_wrong_shipment_join_changes_denominator(self):
        self.assertEqual(wrong_shipment_join(JULY), Counts(90, 101))
        self.assertEqual(wrong_shipment_join(AUGUST), Counts(81, 101))
        for snapshot in (JULY, AUGUST):
            self.assertNotEqual(wrong_shipment_join(snapshot).due, report(snapshot)["Total"].due)
            self.assertNotEqual(wrong_shipment_join(snapshot).rate, report(snapshot)["Total"].rate)


def main() -> int:
    july, august = report(JULY), report(AUGUST)
    print(f"SYNTHETIC EXAMPLE | on_time_order_rate v{METRIC_VERSION}")
    print("Input basis: frozen certified fixture; strategic cohort/hierarchy as of 2026-07-01.")
    print("Region   July on time / due   July rate   August on time / due   August rate")
    for region in (*REGIONS, "Total"):
        j, a = july[region], august[region]
        print(f"{region:<8} {j.on_time:>3} / {j.due:<3}             {float(j.rate):>6.0%}      {a.on_time:>3} / {a.due:<3}               {float(a.rate):>6.0%}")
    print(f"August at July regional weights: {float(fixed_mix_rate(july, august)):.0%}")
    print("Aggregate change: -10 percentage points; each regional rate is unchanged.")
    print("Wrong shipment join: July 90/101; August 81/101 (incorrect order denominators).")
    print("Scope: arithmetic and contract checks only; no security, replay, or production claim.\n")
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
