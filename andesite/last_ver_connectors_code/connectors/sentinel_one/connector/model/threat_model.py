from typing import Any, Dict

from common.utils.pydantic_helper import CamelModel

from connectors.sentinel_one.connector.model.base import (
    OptionalBool,
    OptionalInt,
    OptionalList,
    OptionalObj,
    OptionalStr,
)


class Description(CamelModel):
    read_only: OptionalBool
    description: OptionalStr


class MacroModule(CamelModel):
    module_name: OptionalStr
    sha256: OptionalStr
    sha1: OptionalStr


class DetectionEngine(CamelModel):
    key: OptionalStr
    title: OptionalStr


class ThreatInfo(CamelModel):
    analyst_verdict_description: OptionalStr
    analyst_verdict: OptionalStr
    automatically_resolved: OptionalBool
    browser_type: OptionalStr
    certificate_id: OptionalStr
    classification_source: OptionalStr
    classification: OptionalStr
    cloud_files_hash_verdict: OptionalStr
    collection_id: OptionalStr
    confidence_level: OptionalStr
    created_at: OptionalStr
    detection_engines: OptionalList[DetectionEngine]
    detection_type: OptionalStr
    engines: OptionalList[str]
    external_ticket_exists: OptionalBool
    external_ticket_id: OptionalStr
    failed_actions: OptionalBool
    file_extension_type: OptionalStr
    file_extension: OptionalStr
    file_path: OptionalStr
    file_size: OptionalInt
    file_verification_type: OptionalStr
    identified_at: OptionalStr
    incident_status_description: OptionalStr
    incident_status: OptionalStr
    initiated_by_description: OptionalStr
    initiated_by: OptionalStr
    initiating_user_id: OptionalStr
    initiating_username: OptionalStr
    is_fileless: OptionalBool
    is_valid_certificate: OptionalBool
    macro_modules: OptionalList[MacroModule]
    malicious_process_arguments: OptionalStr
    md5: OptionalStr
    mitigated_preemptively: OptionalBool
    mitigation_status_description: OptionalStr
    mitigation_status: OptionalStr
    originator_process: OptionalStr
    pending_actions: OptionalBool
    process_user: OptionalStr
    publisher_name: OptionalStr
    reached_events_limit: OptionalBool
    reboot_required: OptionalBool
    root_process_upn: OptionalStr
    sha1: OptionalStr
    sha256: OptionalStr
    storyline: OptionalStr
    threat_id: OptionalStr
    threat_name: OptionalStr
    updated_at: OptionalStr


class Technique(CamelModel):
    link: OptionalStr
    name: OptionalStr


class Tactic(CamelModel):
    source: OptionalStr
    name: OptionalStr
    techniques: OptionalList[Technique]


class Indicator(CamelModel):
    ids: OptionalList[int]
    category: OptionalStr
    description: OptionalStr
    tactics: OptionalList[Tactic]
    category_id: OptionalInt


class AgentDetectionInfo(CamelModel):
    account_id: OptionalStr
    account_name: OptionalStr
    agent_detection_state: OptionalStr
    agent_domain: OptionalStr
    agent_ip_v4: OptionalStr
    agent_ip_v6: OptionalStr
    agent_last_logged_in_upn: OptionalStr
    agent_last_logged_in_user_mail: OptionalStr
    agent_last_logged_in_user_name: OptionalStr
    agent_mitigation_mode: OptionalStr
    agent_os_name: OptionalStr
    agent_os_revision: OptionalStr
    agent_registered_at: OptionalStr
    agent_uuid: OptionalStr
    agent_version: OptionalStr
    asset_version: OptionalStr
    cloud_providers: Any
    external_ip: OptionalStr
    group_id: OptionalStr
    group_name: OptionalStr
    site_id: OptionalStr
    site_name: OptionalStr


class ActionCounters(CamelModel):
    failed: OptionalInt
    not_found: OptionalInt
    pending_reboot: OptionalInt
    success: OptionalInt
    total: OptionalInt


class MitigationStatusEntry(CamelModel):
    action: OptionalStr
    actions_counters: OptionalObj[ActionCounters]
    agent_supports_report: OptionalBool
    group_not_found: OptionalBool
    last_update: OptionalStr
    latest_report: OptionalStr
    mitigation_ended_at: OptionalStr
    mitigation_started_at: OptionalStr
    report_id: OptionalStr
    status: OptionalStr


class EcsInfo(CamelModel):
    cluster_name: OptionalStr
    service_arn: OptionalStr
    service_name: OptionalStr
    task_arn: OptionalStr
    task_availability_zone: OptionalStr
    task_definition_arn: OptionalStr
    task_definition_family: OptionalStr
    task_definition_revision: OptionalStr
    type: OptionalStr
    version: OptionalStr


class ContainerInfo(CamelModel):
    id: OptionalStr
    image: OptionalStr
    is_container_quarantine: OptionalBool
    labels: OptionalList[str]
    name: OptionalStr


class KubernetesInfo(CamelModel):
    cluster: OptionalStr
    controller_kind: OptionalStr
    controller_labels: OptionalList[str]
    controller_name: OptionalStr
    is_container_quarantine: OptionalBool
    namespace_labels: OptionalList[str]
    namespace: OptionalStr
    node_labels: OptionalList[str]
    node: OptionalStr
    pod_labels: OptionalList[str]
    pod: OptionalStr


class NetworkInterface(CamelModel):
    id: OptionalStr
    inet: OptionalList[str]
    inet6: OptionalList[str]
    name: OptionalStr
    physical: OptionalStr


class AgentRealtimeInfo(CamelModel):
    account_id: OptionalStr
    account_name: OptionalStr
    active_threats: OptionalInt
    agent_computer_name: OptionalStr
    agent_decommissioned_at: OptionalBool
    agent_domain: OptionalStr
    agent_id: OptionalStr
    agent_infected: OptionalBool
    agent_is_active: OptionalBool
    agent_is_decommissioned: OptionalBool
    agent_machine_type: OptionalStr
    agent_mitigation_mode: OptionalStr
    agent_network_status: OptionalStr
    agent_os_name: OptionalStr
    agent_os_revision: OptionalStr
    agent_os_type: OptionalStr
    agent_uuid: OptionalStr
    agent_version: OptionalStr
    group_id: OptionalStr
    group_name: OptionalStr
    network_interfaces: OptionalList[NetworkInterface]
    operational_state: OptionalStr
    reboot_required: OptionalBool
    scan_aborted_at: OptionalStr
    scan_finished_at: OptionalStr
    scan_started_at: OptionalStr
    scan_status: OptionalStr
    site_id: OptionalStr
    site_name: OptionalStr
    storage_name: OptionalStr
    storage_type: OptionalStr
    user_actions_needed: OptionalList[Dict[str, Any]]


class SentinelOneThreat(CamelModel):
    id: OptionalStr
    agent_detection_info: OptionalObj[AgentDetectionInfo]
    agent_realtime_info: OptionalObj[AgentRealtimeInfo]
    container_info: OptionalObj[ContainerInfo]
    ecs_info: OptionalObj[EcsInfo]
    indicators: OptionalList[Indicator]
    kubernetes_info: OptionalObj[KubernetesInfo]
    mitigation_status: OptionalList[MitigationStatusEntry]
    threat_info: OptionalObj[ThreatInfo]
    whitening_options: OptionalList[str]
