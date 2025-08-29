"""Export summary model for incident/threat hunt reports."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class IncidentSummaryTemplate(BaseModel):
    """Pydantic model for structured incident/threat_hunt report data."""

    title: str = Field(
        default=...,
        description="Clear, concise title describing the core issue (e.g., 'Phishing Campaign Targeting Finance Department')",
    )
    summary: str = Field(
        default=...,
        description="Executive summary in 2-3 sentences. Include impact, scope, and current status.",
    )
    details: str = Field(
        default=...,
        description="Detailed technical analysis including timeline, attack vectors, and observed indicators. Be factual and thorough while maintaining clarity.",
    )
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        default=...,
        description="Assess incident/threat severity based on impact, scope, and data sensitivity. Consider business impact, number of affected systems/users, and data criticality.",
    )
    classification: Literal["Intentional", "Accidental", "Unknown"] = Field(
        default=...,
        description="Classification of incident/threat intent",
    )
    priority: Literal["Low", "Medium", "High", "Critical"] = Field(
        default=...,
        description="Urgency of response needed. Consider time sensitivity, business impact, and potential for escalation.",
    )
    status: Literal["New", "In Progress", "Resolved", "Closed"] = Field(
        default="New",
        description="Current state of incident/threat handling and remediation progress.",
    )
    category: str = Field(
        default=...,
        description="Primary incident/threat type (e.g., Malware, Phishing, Data Breach, DDoS, Unauthorized Access)",
    )
    mitre_attack_model: str = Field(
        default=...,
        description="The relevant MITRE ATT&CK technique ID and name (e.g., T1566 - Phishing)",
    )
    mitre_tactics: list[str] = Field(
        default_factory=list,
        description="List of MITRE ATT&CK tactics involved in the incident/threat",
    )
    detection_method: str = Field(
        default=...,
        description="How the incident/threat was discovered (e.g., SIEM Alert, User Report, Automated Detection)",
    )
    source: str = Field(
        default=...,
        description="Initial entry point or source of the incident/threat",
    )
    target_asset_type: list[str] = Field(
        default=...,
        description="Categories of affected assets (e.g., Workstations, Servers, Network Devices, Cloud Resources)",
    )
    target_assets: list[str] = Field(
        default_factory=list,
        description="Specific affected assets with identifiers where known",
    )
    affected_users: list[str] = Field(
        default_factory=list,
        description="Impacted user accounts or groups",
    )
    threat_actor: Literal["Internal", "External", "Unknown"] = Field(
        default=...,
        description="Classification of threat actor origin",
    )
    actions_taken: list[str] = Field(
        default=...,
        description="What actions were taken to resolve or investigate the incident/threat. Be concise. Stick to the facts and only the facts, but do not exclude any relevant details. Unless you have clear evidence that an action was performed, do not include it.",
    )
    data_breach: bool = Field(
        default=False,
        description="Whether the incident/threat involved unauthorized access to sensitive data",
    )
    evidence_location: str | None = Field(
        default=None,
        description="Where relevant logs, forensic data, or other evidence is stored",
    )

    @field_validator("severity", "priority", "classification", "threat_actor", "status")
    @classmethod
    def validate_first_letter_titled(cls, v: str) -> str:
        """Ensures everything is properly titled"""
        return v.title()
