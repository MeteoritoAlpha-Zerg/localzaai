from common.utils.pydantic_helper import CamelModel
from pydantic import Field

from connectors.sentinel_one.connector.model.base import (
    OptionalBool,
    OptionalObj,
    OptionalStr,
)


class ContainerInfo(CamelModel):
    id: OptionalStr
    image: OptionalStr
    name: OptionalStr
    labels: OptionalStr


class ProcessInfo(CamelModel):
    commandline: OptionalStr
    effective_user: OptionalStr
    file_hash_md5: OptionalStr
    file_hash_sha1: OptionalStr
    file_hash_sha256: OptionalStr
    file_path: OptionalStr
    file_signer_identity: OptionalStr
    integrity_level: OptionalStr
    login_user: OptionalStr
    name: OptionalStr
    pid_starttime: OptionalStr
    pid: OptionalStr
    real_user: OptionalStr
    storyline: OptionalStr
    subsystem: OptionalStr
    unique_id: OptionalStr
    user: OptionalStr


class RuleInfo(CamelModel):
    description: OptionalStr
    id: OptionalStr
    name: OptionalStr
    query_lang: OptionalStr
    query_type: OptionalStr
    s1ql: OptionalStr = Field(serialization_alias="s1ql")  # CamelModel will serialize as s1Ql w/o alias
    scope_level: OptionalStr
    severity: OptionalStr
    treat_as_threat: OptionalStr


class KubernetesInfo(CamelModel):
    cluster: OptionalStr
    controller_kind: OptionalStr
    controller_labels: OptionalStr
    controller_name: OptionalStr
    namespace_labels: OptionalStr
    namespace: OptionalStr
    node: OptionalStr
    pod_labels: OptionalStr
    pod: OptionalStr


class AgentRealtimeInfo(CamelModel):
    id: OptionalStr
    infected: OptionalBool
    is_active: OptionalBool
    is_decommissioned: OptionalBool
    machine_type: OptionalStr
    name: OptionalStr
    os: OptionalStr
    uuid: OptionalStr


class AgentDetectionInfo(CamelModel):
    account_id: OptionalStr
    machine_type: OptionalStr
    name: OptionalStr
    os_family: OptionalStr
    os_name: OptionalStr
    os_revision: OptionalStr
    site_id: OptionalStr
    uuid: OptionalStr
    version: OptionalStr


class TargetProcessInfo(CamelModel):
    tgt_file_hash_sha256: OptionalStr
    tgt_proc_pid: OptionalStr
    tgt_file_modified_at: OptionalStr
    tgt_file_id: OptionalStr
    tgt_proc_name: OptionalStr
    tgt_proc_integrity_level: OptionalStr
    tgt_process_start_time: OptionalStr
    tgt_file_hash_sha1: OptionalStr
    tgt_proc_storyline_id: OptionalStr
    tgt_proc_cmd_line: OptionalStr
    tgt_file_created_at: OptionalStr
    tgt_file_is_signed: OptionalStr
    tgt_file_path: OptionalStr
    tgt_file_old_path: OptionalStr
    tgt_proc_image_path: OptionalStr
    tgt_proc_signed_status: OptionalStr
    tgt_proc_uid: OptionalStr


class AlertInfo(CamelModel):
    alert_id: OptionalStr
    analyst_verdict: OptionalStr
    created_at: OptionalStr
    dns_request: OptionalStr
    dns_response: OptionalStr
    dst_ip: OptionalStr
    dst_port: OptionalStr
    dv_event_id: OptionalStr
    event_type: OptionalStr
    hit_type: OptionalStr
    incident_status: OptionalStr
    indicator_category: OptionalStr
    indicator_description: OptionalStr
    indicator_name: OptionalStr
    is_edr: OptionalBool
    login_account_domain: OptionalStr
    login_account_sid: OptionalStr
    login_is_administrator_equivalent: OptionalStr
    login_is_successful: OptionalStr
    login_type: OptionalStr
    logins_user_name: OptionalStr
    module_path: OptionalStr
    module_sha1: OptionalStr
    net_event_direction: OptionalStr
    registry_key_path: OptionalStr
    registry_old_value_type: OptionalStr
    registry_old_value: OptionalStr
    registry_path: OptionalStr
    registry_value: OptionalStr
    reported_at: OptionalStr
    source: OptionalStr
    src_ip: OptionalStr
    src_machine_ip: OptionalStr
    src_port: OptionalStr
    ti_indicator_comparison_method: OptionalStr
    ti_indicator_source: OptionalStr
    ti_indicator_type: OptionalStr
    ti_indicator_value: OptionalStr
    updated_at: OptionalStr


class SentinelOneAlert(CamelModel):
    agent_detection_info: OptionalObj[AgentDetectionInfo]
    agent_realtime_info: OptionalObj[AgentRealtimeInfo]
    alert_info: OptionalObj[AlertInfo]
    container_info: OptionalObj[ContainerInfo]
    kubernetes_info: OptionalObj[KubernetesInfo]
    rule_info: OptionalObj[RuleInfo]
    source_parent_process_info: OptionalObj[ProcessInfo]
    source_process_info: OptionalObj[ProcessInfo]
    target_process_info: OptionalObj[TargetProcessInfo]
