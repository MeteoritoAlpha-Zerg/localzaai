import unittest

from connectors.splunk.database.splunk_instance import SplunkInstance
from connectors.splunk.database.utils import change_authorization_token_type


class TestSplunkInstance(unittest.TestCase):
    def test_sparse_table_conversion_preserves_order(self):
        res = [
            {"src_ip": "value11", "dest_ip": "value12", "analytic_story": "value13"},
            {"src_ip": "value21", "dest_ip": "value22", "analytic_story": "value23"},
            {"src_ip": "value31", "dest_ip": "value32", "analytic_story": "value33"},
        ]

        columns, rows = SplunkInstance.result_to_sparse_table(res)
        self.assertEqual(len(columns), 3)
        self.assertEqual(len(rows), 3)
        self.assertEqual(columns, ["src_ip", "dest_ip", "analytic_story"])
        self.assertEqual(
            rows,
            [
                ["value11", "value12", "value13"],
                ["value21", "value22", "value23"],
                ["value31", "value32", "value33"],
            ],
        )

    @unittest.skip("Manual test only")
    async def test_create_notable_alert(self):
        si = SplunkInstance(
            protocol="https",
            host="18.222.249.79",
            port=8089,
            token="",
            app="-",
            ssl_verification=False,
        )

        await si.create_notable_alert(
            "AN-1001",
            'test "title"',
            "test description",
            "test category",
            [("doc_id", "abcdef1234567890"), ("andesite_priority", "15")],
        )

    def test_change_auth_token_type(self):
        old = [("Authorization", "Splunk foobar")]

        output = change_authorization_token_type("Splunk", "Bearer", old)

        assert output == [("Authorization", "Bearer foobar")]
