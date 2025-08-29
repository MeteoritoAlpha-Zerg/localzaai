fake_censys_records = [
    {
        "host_identifier": {"ipv4": "192.0.2.1"},
        "date": "2024-10-15",
        "l2": 0.879,
        "location": {"country": "United States"},
        "services": [
            {
                "port": 443,
                "service_name": "https",
                "transport": "tcp",
                "software": [{"uniform_resource_identifier": "nginx/1.21.0"}],
            }
        ],
        "operating_system": {"uniform_resource_identifier": "Ubuntu 20.04"},
        "dns": {"names": ["example.com", "www.example.com"]},
    },
    {
        "host_identifier": {"ipv4": "203.0.113.45"},
        "date": "2024-10-14",
        "l2": 0.457,
        "location": {"country": "Japan"},
        "services": [
            {
                "port": 22,
                "service_name": "ssh",
                "transport": "tcp",
                "software": [{"uniform_resource_identifier": "OpenSSH 8.2"}],
            }
        ],
        "operating_system": {"uniform_resource_identifier": "Debian 10"},
        "dns": {"names": ["myserver.jp"]},
    },
    {
        "host_identifier": {"ipv4": "198.51.100.2"},
        "date": "2024-10-13",
        "l2": 0.638,
        "location": {"country": "Germany"},
        "services": [
            {
                "port": 80,
                "service_name": "http",
                "transport": "tcp",
                "software": [{"uniform_resource_identifier": "Apache/2.4.41"}],
            },
            {"port": 25, "service_name": "smtp", "transport": "tcp", "software": []},
        ],
        "operating_system": {"uniform_resource_identifier": "Windows Server 2016"},
        "dns": {"names": ["web.de", "mail.web.de"]},
    },
]


formatted_censys_records = [
    {
        "ip": "192.0.2.1",
        "snapshot_date": "2024-10-15",
        "l2": 0.879,
        "services": [
            {
                "port": 443,
                "service_name": "https",
                "transport": "tcp",
                "software": "nginx/1.21.0",
            }
        ],
        "location": "United States",
        "operating_system": "Ubuntu 20.04",
        "dns": ["example.com", "www.example.com"],
    },
    {
        "ip": "203.0.113.45",
        "snapshot_date": "2024-10-14",
        "l2": 0.457,
        "services": [
            {
                "port": 22,
                "service_name": "ssh",
                "transport": "tcp",
                "software": "OpenSSH 8.2",
            }
        ],
        "location": "Japan",
        "operating_system": "Debian 10",
        "dns": ["myserver.jp"],
    },
    {
        "ip": "198.51.100.2",
        "snapshot_date": "2024-10-13",
        "l2": 0.638,
        "services": [
            {
                "port": 80,
                "service_name": "http",
                "transport": "tcp",
                "software": "Apache/2.4.41",
            },
            {"port": 25, "service_name": "smtp", "transport": "tcp", "software": None},
        ],
        "location": "Germany",
        "operating_system": "Windows Server 2016",
        "dns": ["web.de", "mail.web.de"],
    },
]
