from connectors.proofpoint.client.proofpoint_instance import Interval


class TestIntervalOverlaps:
    def test_overlaps_with_complete_overlap(self):
        """Test when intervals completely overlap (identical)"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T12:00:00Z")
        interval2 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T12:00:00Z")
        assert interval1.overlaps_with(interval2)
        assert interval2.overlaps_with(interval1)

    def test_overlaps_with_partial_overlap(self):
        """Test when intervals partially overlap"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T12:00:00Z")
        interval2 = Interval(interval="2025-06-20T06:00:00Z/2025-06-20T18:00:00Z")
        assert interval1.overlaps_with(interval2)
        assert interval2.overlaps_with(interval1)

    def test_overlaps_with_no_overlap_before(self):
        """Test when intervals don't overlap - first ends before second starts"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T06:00:00Z")
        interval2 = Interval(interval="2025-06-20T12:00:00Z/2025-06-20T18:00:00Z")
        assert not interval1.overlaps_with(interval2)
        assert not interval2.overlaps_with(interval1)

    def test_overlaps_with_no_overlap_after(self):
        """Test when intervals don't overlap - first starts after second ends"""
        interval1 = Interval(interval="2025-06-20T12:00:00Z/2025-06-20T18:00:00Z")
        interval2 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T06:00:00Z")
        assert not interval1.overlaps_with(interval2)
        assert not interval2.overlaps_with(interval1)

    def test_overlaps_with_touching_intervals(self):
        """Test when intervals touch exactly at boundaries (should not overlap)"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T12:00:00Z")
        interval2 = Interval(interval="2025-06-20T12:00:00Z/2025-06-20T18:00:00Z")
        assert not interval1.overlaps_with(interval2)
        assert not interval2.overlaps_with(interval1)

    def test_overlaps_with_one_contains_other(self):
        """Test when one interval completely contains another"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T18:00:00Z")
        interval2 = Interval(interval="2025-06-20T06:00:00Z/2025-06-20T12:00:00Z")
        assert interval1.overlaps_with(interval2)
        assert interval2.overlaps_with(interval1)

    def test_overlaps_with_minimal_overlap(self):
        """Test minimal overlap (1 second)"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T12:00:01Z")
        interval2 = Interval(interval="2025-06-20T12:00:00Z/2025-06-20T18:00:00Z")
        assert interval1.overlaps_with(interval2)
        assert interval2.overlaps_with(interval1)

    def test_overlaps_with_different_days(self):
        """Test intervals on different days"""
        interval1 = Interval(interval="2025-06-20T00:00:00Z/2025-06-20T23:59:59Z")
        interval2 = Interval(interval="2025-06-21T00:00:00Z/2025-06-21T23:59:59Z")
        assert not interval1.overlaps_with(interval2)
        assert not interval2.overlaps_with(interval1)

    def test_overlaps_with_cross_day_boundary(self):
        """Test intervals that cross day boundaries"""
        interval1 = Interval(interval="2025-06-20T18:00:00Z/2025-06-21T06:00:00Z")
        interval2 = Interval(interval="2025-06-20T22:00:00Z/2025-06-21T02:00:00Z")
        assert interval1.overlaps_with(interval2)
        assert interval2.overlaps_with(interval1)
