from typing import Optional, Union
from pydantic import BaseModel


class ScopeTargetDefinition(BaseModel):
    """
    Represents the relationships, dependencies and functionality of each selector.
    """

    name: str
    multiselect: bool = False
    depends_on: Optional[str] = None


class ScopeTargetSelector(BaseModel):
    """
    This defines the possible tree values that can be selected for a given dataset target.
    """

    type: str
    values: Union[dict[str, list["ScopeTargetSelector"]], list[str]]


class ConnectorQueryTargetOptions(BaseModel):
    definitions: list[ScopeTargetDefinition]
    selectors: list[ScopeTargetSelector]


"""
Example API response for ConnectorQueryTargetOptions:

{
    "definitions": [
        {
            "name": "catalog",
            "multiselect": false,
            "dependsOn": null
        },
        {
            "name": "database",
            "multiselect": false,
            "dependsOn": "catalog"
        },
        {
            "name": "tables",
            "multiselect": true,
            "dependsOn": "database"
        },
        {
            "name": "workgroup",
            "multiselect": false,
            "dependsOn": null
        }
    ],
    "selectors": [
        {
            "type": "catalog",
            "values": {
                "AwsDataCatalog": [
                    {
                        "type": "database",
                        "values": {
                            "bots-01": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "fgt_event",
                                        "fgt_traffic",
                                        "fgt_utm",
                                        "iis",
                                        "nessus_scan",
                                        "stream_dhcp",
                                        "stream_dns",
                                        "stream_http",
                                        "stream_icmp",
                                        "stream_ip",
                                        "stream_ldap",
                                        "stream_mapi",
                                        "stream_sip",
                                        "stream_smb",
                                        "stream_snmp",
                                        "stream_tcp",
                                        "suricata",
                                        "wineventlog_application",
                                        "wineventlog_security",
                                        "wineventlog_system",
                                        "winregistry",
                                        "xmlwineventlog"
                                    ]
                                }
                            ],
                            "censys": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "combined"
                                    ]
                                }
                            ],
                            "ciciot2023-test": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "cic-iot-partitionedcic_iot"
                                    ]
                                }
                            ],
                            "cloudwatch": [
                                {
                                    "type": "tables",
                                    "values": []
                                }
                            ],
                            "copilot-test": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "copilot_demo_v1_test"
                                    ]
                                }
                            ],
                            "dashboard": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "host_metrics",
                                        "hosts",
                                        "operating_metrics"
                                    ]
                                }
                            ],
                            "default": [
                                {
                                    "type": "tables",
                                    "values": []
                                }
                            ],
                            "equinox": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "ip_stability"
                                    ]
                                }
                            ],
                            "ipinfo": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "asn",
                                        "combined",
                                        "combined_79a8fef2812d187b5b63c89042af225b",
                                        "combined_historical",
                                        "company",
                                        "company_location",
                                        "domains",
                                        "location",
                                        "privacy"
                                    ]
                                }
                            ],
                            "metamorph-eval": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "metamorph_model_eval"
                                    ]
                                }
                            ],
                            "metamorph-eval-doc": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "metamorph_model_eval_doc"
                                    ]
                                }
                            ],
                            "mm_category": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "no_category_data"
                                    ]
                                }
                            ],
                            "service_classification": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "data",
                                        "data_no_category"
                                    ]
                                }
                            ],
                            "spark_demo_database": [
                                {
                                    "type": "tables",
                                    "values": []
                                }
                            ],
                            "unsw": [
                                {
                                    "type": "tables",
                                    "values": [
                                        "uber_table"
                                    ]
                                }
                            ]
                        }
                    }
                ]
            }
        },
        {
            "type": "workgroup",
            "values": [
                "athena-spark",
                "primary",
                "shasta"
            ]
        }
    ]
}
"""
