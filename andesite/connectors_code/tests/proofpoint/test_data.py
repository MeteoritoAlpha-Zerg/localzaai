from httpx import Request, Response


def get_test_single_page_response_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={"campaigns": [{"id": "campaign_id_1"}, {"id": "campaign_id_2"}]},
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com"),
            json={"campaigns": []},
        ),
    ]


def get_test_get_campaigns_multiple_days_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day1&page1"),
            json={
                "campaigns": [
                    {"id": "campaign_id_1", "datetime": "2020-05-01T01:15:00Z"},
                    {"id": "campaign_id_2", "datetime": "2020-05-01T02:35:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day1&page2"),
            json={"campaigns": []},
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day2&page1"),
            json={
                "campaigns": [
                    {"id": "campaign_id_3", "datetime": "2020-05-02T01:15:00Z"},
                    {"id": "campaign_id_4", "datetime": "2020-05-02T02:35:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day2&page2"),
            json={"campaigns": []},
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day3&page1"),
            json={
                "campaigns": [
                    {"id": "campaign_id_5", "datetime": "2020-05-03T01:15:00Z"},
                    {"id": "campaign_id_6", "datetime": "2020-05-03T02:35:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com/v2/campaign/ids/day3&page2"),
            json={"campaigns": []},
        ),
    ]


def get_test_get_campaigns_pagination_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_1", "datetime": "2020-05-01T01:15:00Z"},
                    {"id": "campaign_id_2", "datetime": "2020-05-01T02:35:00Z"},
                ]
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_3", "datetime": "2020-05-01T03:15:00Z"},
                    {"id": "campaign_id_4", "datetime": "2020-05-01T04:35:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com"),
            json={"campaigns": []},
        ),
    ]


def get_test_get_campaigns_pagination_multiday_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_1", "datetime": "2020-05-01T01:15:00Z"},
                    {"id": "campaign_id_2", "datetime": "2020-05-01T02:35:00Z"},
                ]
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_3", "datetime": "2020-05-01T03:15:00Z"},
                    {"id": "campaign_id_4", "datetime": "2020-05-01T04:35:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com"),
            json={"campaigns": []},
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_5", "datetime": "2020-05-02T01:15:00Z"},
                    {"id": "campaign_id_6", "datetime": "2020-05-02T02:35:00Z"},
                ]
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "campaigns": [
                    {"id": "campaign_id_7", "datetime": "2020-05-02T03:15:00Z"},
                ]
            },
        ),
        Response(
            404,
            request=Request("GET", "https://test_url.com"),
            json={"campaigns": []},
        ),
    ]


def get_test_get_siem_events_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "messagesBlocked": [
                    {
                        "messageTime": "2020-05-01T01:15:00Z",
                        "senderIP": "123.456.789.101",
                        "messageParts": [
                            {
                                "disposition": "attached",
                                "filename": "attachment1.txt",
                            },
                            {
                                "disposition": "inline",
                                "filename": "html.txt",
                            },
                        ],
                    },
                    {"messageTime": "2020-05-01T02:15:00Z", "senderIP": "12.56.19.21"},
                ],
                "messagesDelivered": [
                    {"messageTime": "2020-05-01T03:15:00Z", "senderIP": "10.456.789.01"},
                ],
                "clicksBlocked": [
                    {"clickTime": "2020-05-01T03:15:00Z", "senderIP": "123.56.79.101", "classification": "phish"},
                ],
                "clicksDelivered": [
                    {"clickTime": "2020-05-01T03:15:00Z", "senderIP": "15.45.89.1", "classification": "not phish"},
                ],
            },
        ),
    ]


def get_test_get_forensics_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "reports": [
                    {
                        "threat_id": "abc123",
                        "forensics": [
                            {
                                "type": "virus",
                                "display": "you have a virus",
                                "what": "BadVirus",
                                "platform": "windows",
                                "malicious": True,
                            },
                            {
                                "type": "file",
                                "display": "you have a file",
                                "what": "an allowed file",
                                "platform": "linux",
                                "malicious": False,
                            },
                        ],
                    },
                    {
                        "threat_id": "def456",
                        "forensics": [
                            {
                                "type": "virus",
                                "display": "you have another virus",
                                "what": "AReallyBadVirus",
                                "platform": "windows",
                                "malicious": True,
                            },
                            {
                                "type": "file",
                                "display": "you have a file",
                                "what": "an allowed file",
                                "platform": "linux",
                                "malicious": False,
                            },
                        ],
                    },
                ],
            },
        ),
    ]


def get_test_find_iocs_in_siem_events_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com"),
            json={
                "messagesBlocked": [
                    {
                        "messageTime": "2020-05-01T01:15:00Z",
                        "senderIP": "123.456.789.101",
                        "ccAddress": "IT@yourdomain.ai",
                        "subject": "THIS IS LEGIT! Open this attachment before tomorrow!",
                        "messageParts": [
                            {
                                "disposition": "attached",
                                "filename": "attachment1.txt",
                            },
                            {
                                "disposition": "inline",
                                "filename": "html.txt",
                            },
                        ],
                    },
                    {"messageTime": "2020-05-01T02:15:00Z", "senderIP": "12.56.19.21"},
                ],
                "messagesDelivered": [
                    {"messageTime": "2020-05-01T03:15:00Z", "senderIP": "10.456.789.01"},
                ],
                "clicksBlocked": [
                    {
                        "clickTime": "2020-05-01T03:15:00Z",
                        "senderIP": "123.56.79.101",
                        "classification": "phish",
                        "sender": "IT@closetoyourdomain.ai",
                    },
                ],
                "clicksDelivered": [
                    {"clickTime": "2020-05-01T03:15:00Z", "senderIP": "15.45.89.1", "classification": "not phish"},
                ],
            },
        ),
    ]


def get_test_find_iocs_in_campaigns_data():
    return [
        Response(
            200,
            request=Request("GET", "https://test_url.com/camapign/campaign_id_1"),
            json={
                "id": "campaign_id_1",
                "datetime": "2020-05-01T01:15:00Z",
                "status": "active",
                "description": "This is a test campaign. Look for the following iocs: 'this/command/hacks.exe', 'abc-123-def-456-ghi', 'ashadydomain.ru'",
                "campaignMembers": ["actor1", "actor2"],
            },
        ),
        Response(
            200,
            request=Request("GET", "https://test_url.com/camapign/campaign_id_2"),
            json={
                "id": "campaign_id_2",
                "datetime": "2020-05-01T01:15:00Z",
                "status": "inactive",
                "description": "This is another test campaign",
                "campaignMembers": ["actor3", "actor4"],
            },
        ),
    ]
