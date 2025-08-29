import unittest

from common.utils.list_helper import find_insertion_index, insert_and_maintain_order


class TestListHelpers(unittest.TestCase):
    def test_simple_find_insertion_index(self):
        sorted_list = [1, 3]

        assert find_insertion_index(sorted_list=sorted_list, item=4, reverse=False) == 2
        assert (
            find_insertion_index(list(reversed(sorted_list)), 4, lambda x: x, True) == 0
        )

        assert find_insertion_index(sorted_list, 2, lambda x: x, False) == 1
        assert (
            find_insertion_index(list(reversed(sorted_list)), 2, lambda x: x, True) == 1
        )

    def test_key_find_insertion_index(self):
        sorted_list = [{"not-id": 10}, {"id": 1}, {"id": 5}]

        assert (
            find_insertion_index(
                sorted_list, {"id": 3}, lambda x: x.get("id", 0), False
            )
            == 2
        )
        assert (
            find_insertion_index(
                sorted_list, {"uh oh": 3}, lambda x: x.get("id", 0), False
            )
            == 1
        )
        assert (
            find_insertion_index(
                list(reversed(sorted_list)), {"id": 3}, lambda x: x.get("id", 0), True
            )
            == 1
        )

    def test_insert_and_maintain_order(self):
        sorted_list = [1, 3]

        new_list = sorted_list.copy()
        insert_and_maintain_order(new_list, 4, lambda x: x, False)
        assert new_list == [1, 3, 4]
        new_list = list(reversed(sorted_list.copy()))
        insert_and_maintain_order(new_list, 4, lambda x: x, True)
        assert new_list == [4, 3, 1]

        new_list = sorted_list.copy()
        insert_and_maintain_order(new_list, 2, lambda x: x, False)
        assert new_list == [1, 2, 3]
        new_list = list(reversed(sorted_list.copy()))
        insert_and_maintain_order(new_list, 2, lambda x: x, True)
        assert new_list == [3, 2, 1]

        sorted_list = [{"not-id": 10}, {"id": 1}, {"id": 5}]

        new_list = sorted_list.copy()
        insert_and_maintain_order(new_list, {"id": 3}, lambda x: x.get("id", 0), False)
        assert new_list == [{"not-id": 10}, {"id": 1}, {"id": 3}, {"id": 5}]
        new_list = sorted_list.copy()
        insert_and_maintain_order(
            new_list, {"uh oh": 3}, lambda x: x.get("id", 0), False
        )
        assert new_list == [{"not-id": 10}, {"uh oh": 3}, {"id": 1}, {"id": 5}]
        new_list = list(reversed(sorted_list.copy()))
        insert_and_maintain_order(new_list, {"id": 3}, lambda x: x.get("id", 0), True)
        assert new_list == [{"id": 5}, {"id": 3}, {"id": 1}, {"not-id": 10}]
