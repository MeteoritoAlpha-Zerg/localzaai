from typing import Any, Dict

from common.utils.pydantic_helper import CamelModel

from connectors.sentinel_one.connector.model.base import (
    OptionalBool,
    OptionalInt,
    OptionalList,
    OptionalObj,
    OptionalStr,
)


class Note(CamelModel):
    created_at: OptionalStr
    id: OptionalStr
    note: OptionalStr
    resource_id: OptionalStr
    updated_at: OptionalStr
    user_id: OptionalStr
    user_name: OptionalStr


class DeviceReviewLogEntry(CamelModel):
    updated_time: OptionalInt
    current: OptionalStr
    previous: OptionalStr
    reason: OptionalStr
    updated_time_dt: OptionalStr
    username: OptionalStr


class VssVolume(CamelModel):
    diff_area_free_percentage: float
    diff_area_current_allocated_bytes: OptionalInt
    diff_area_current_used_bytes: OptionalInt
    diff_area_max_limit_bytes: OptionalInt
    diff_area_name: OptionalStr


class DiskMetric(CamelModel):
    free_bytes_available_to_caller: OptionalInt
    free_percentage: float
    total_number_of_bytes: OptionalInt
    total_number_of_free_bytes: OptionalInt
    path: OptionalStr
    volume_type: OptionalStr


class Agent(CamelModel):
    agent_version: OptionalStr
    anti_tampering_status: OptionalStr
    configurable_network_quarantine: OptionalBool
    console_connectivity: OptionalBool
    console_migration_status: OptionalStr
    customer_identifier: OptionalStr
    decommissioned: OptionalBool
    detection_state: OptionalStr
    disk_encryption: OptionalBool
    disk_metrics: OptionalList[DiskMetric]
    dv_connectivity: OptionalStr
    firewall_status: OptionalBool
    full_disk_scan_dt: OptionalStr
    health_status: OptionalStr
    id: OptionalStr
    installer_type: OptionalStr
    location: OptionalList[str]
    missing_permissions: OptionalList[str]
    network_status: OptionalStr
    operational_state: OptionalStr
    pending_actions: OptionalList[str]
    pending_uninstall: OptionalBool
    ranger_status: OptionalStr
    ranger_version: OptionalStr
    subscribe_on_dt: OptionalStr
    uninstalled: OptionalBool
    up_to_date: OptionalBool
    uuid: OptionalStr
    vss_last_snapshot_dt: OptionalStr
    vss_protection_status: OptionalStr
    vss_rollback_status: OptionalStr
    vss_service_status: OptionalStr
    vss_volumes: OptionalList[VssVolume]


class NetworkInterface(CamelModel):
    gateway_ip: OptionalStr
    gateway_mac: OptionalStr
    ip: OptionalStr
    mac: OptionalStr
    name: OptionalStr
    network_name: OptionalStr
    subnet: OptionalStr


class Attack(CamelModel):
    name: OptionalStr
    uid: OptionalStr
    version: OptionalStr


class Alert(CamelModel):
    activity: OptionalStr
    attacks: OptionalList[Attack]
    classification: OptionalStr
    count: OptionalInt
    detected_at: OptionalStr
    id: OptionalStr
    name: OptionalStr
    severity: OptionalStr
    status: OptionalStr
    time: OptionalInt


class Application(CamelModel):
    name: OptionalStr
    version: OptionalStr
    vendor_name: OptionalStr
    installed_time_dt: OptionalStr


class SentinelOneEndpoint(CamelModel):
    active_coverage: OptionalList[str]
    agent: OptionalObj[Agent]
    alerts_count: OptionalList[Alert]
    alerts: OptionalList[Alert]
    applications: OptionalList[Application]
    architecture: OptionalStr
    asset_contact_email: OptionalStr
    asset_criticality: OptionalStr
    asset_environment: OptionalStr
    asset_status: OptionalStr
    category: OptionalStr
    core_count: OptionalInt
    cpu: OptionalStr
    device_review_log: OptionalList[DeviceReviewLogEntry]
    device_review: OptionalStr
    domain: OptionalStr
    first_seen_dt: OptionalStr
    gateway_ips: OptionalList[str]
    gateway_macs: OptionalList[str]
    hostnames: OptionalList[str]
    id_secondary: OptionalList[str]
    id: OptionalStr
    internal_ips_v6: OptionalList[str]
    internal_ips: OptionalList[str]
    ip_address: OptionalStr
    is_ad_connector: OptionalBool
    last_active_dt: OptionalStr
    last_reboot_dt: OptionalStr
    mac_addresses: OptionalList[str]
    memory_readable: OptionalStr
    memory: OptionalInt
    missing_coverage: OptionalList[str]
    name: OptionalStr
    network_interfaces: OptionalList[NetworkInterface]
    notes: OptionalList[Note]
    os_family: OptionalStr
    os_name_version: OptionalStr
    os_version: OptionalStr
    os: OptionalStr
    resource_type: OptionalStr
    risk_factors: OptionalList[str]
    s1_account_id: OptionalStr
    s1_account_name: OptionalStr
    s1_group_id: OptionalStr
    s1_group_name: OptionalStr
    s1_management_id: OptionalInt
    s1_scope_id: OptionalStr
    s1_scope_level: OptionalStr
    s1_scope_path: OptionalStr
    s1_scope_type: OptionalInt
    s1_site_id: OptionalStr
    s1_site_name: OptionalStr
    s1_updated_at: OptionalStr
    serial_number: OptionalStr
    sub_category: OptionalStr
    subnets: OptionalList[str]
    surfaces: OptionalList[str]
    tags: OptionalList[Dict[str, Any]]
