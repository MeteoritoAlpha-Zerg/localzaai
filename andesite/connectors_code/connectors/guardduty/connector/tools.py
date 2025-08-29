from common.jsonlogging.jsonlogger import Logging
import asyncio
from typing import Any
import boto3
from botocore.config import Config as BotoConfig
from opentelemetry import trace
from common.models.tool import Tool, ToolResult
from common.models.connector_id_enum import ConnectorIdEnum
from connectors.guardduty.connector.config import GuarddutyConnectorConfig
from connectors.guardduty.connector.target import GuarddutyTarget
from connectors.guardduty.connector.secrets import GuarddutySecrets
from connectors.tools import ConnectorToolsInterface
from pydantic import BaseModel, Field

tracer = trace.get_tracer(__name__)
logger = Logging.get_logger(__name__)

class GetGuarddutyFindingsInput(BaseModel):
    """
    Input model for listing GuardDuty findings.

    detector_id: The detector ID to list findings for.
    """
    detector_id: str = Field(
        description="The detector ID to list findings for"
    )

class GetFindingDetailsInput(BaseModel):
    """
    Input model for retrieving GuardDuty finding details.

    detector_id: The detector ID that generated the finding.
    finding_id: The specific finding ID to retrieve details for.
    """
    detector_id: str = Field(
        description="The detector ID"
    )
    finding_id: str = Field(
        description="The finding ID to retrieve details for"
    )

class GuarddutyConnectorTools(ConnectorToolsInterface[GuarddutySecrets]):
    """
    Tools for interacting with AWS GuardDuty: list findings and retrieve finding details.
    """
    def __init__(
        self,
        config: GuarddutyConnectorConfig,
        target: GuarddutyTarget,
        secrets: GuarddutySecrets
    ):
        """
        Initializes the setting for GuardDuty tools.

        :param config: GuarddutyConnectorConfig with AWS credentials and settings.
        :param target: GuarddutyTarget specifying detector IDs for queries.
        """
        self.config = config
        super().__init__(ConnectorIdEnum.GUARDDUTY, target=target, secrets=secrets)

    def get_tools(self) -> list[Tool]:
        """
        Returns the list of tools available for GuardDuty operations.

        :return: list of Tool objects for finding enumeration and detail retrieval.
        """
        return [
            Tool(
                connector=ConnectorIdEnum.GUARDDUTY,
                name="get_guardduty_findings",
                execute_fn=self.get_guardduty_findings_async,
            ),
            Tool(
                connector=ConnectorIdEnum.GUARDDUTY,
                name="get_finding_details",
                execute_fn=self.get_finding_details_async,
            ),
        ]

    def _get_client(self):
        """
        Internal helper to construct a boto3 GuardDuty client with configured retries and timeouts.

        :return: Configured boto3 GuardDuty client.
        """
        boto_config = BotoConfig(
            retries={
                'max_attempts': self.config.api_max_retries,
                'mode': 'standard'
            },
            connect_timeout=self.config.api_request_timeout,
            read_timeout=self.config.api_request_timeout
        )
        return boto3.client(
            "guardduty",
            region_name=self.config.aws_region,
            aws_access_key_id=self._secrets.aws_access_key_id.get_secret_value(),
            aws_secret_access_key=self._secrets.aws_secret_access_key.get_secret_value(),
            aws_session_token=(
                self._secrets.aws_session_token.get_secret_value()
                if self._secrets.aws_session_token
                else None
            ),
            config=boto_config
        )

    @tracer.start_as_current_span("get_guardduty_findings_async")
    async def get_guardduty_findings_async(self, input: GetGuarddutyFindingsInput) -> ToolResult:
        """
        lists GuardDuty findings for the specified detector ID with pagination.

        :param input: GetGuarddutyFindingsInput containing the detector_id
        :return: ToolResult where result is a list of normalized finding dictionaries
        """
        detector_id = input.detector_id
        client = self._get_client()

        # Paginate through findings
        paginator = client.get_paginator("list_findings")
        finding_ids: list[str] = []
        for page in paginator.paginate( DetectorId=detector_id, MaxResults=self.config.findings_max_results):
            item = await asyncio.to_thread(lambda: page)
            finding_ids.extend(item.get("FindingIds", []))

        if not finding_ids:
            return ToolResult(result=[])

        raw_findings = []
        # max request size for aws is 50, beyond that you get a bounds error (probably share with zerg)
        for i in range(0, len(finding_ids), 50):
            response_i = await asyncio.to_thread(
                lambda: client.get_findings(
                    DetectorId=detector_id,
                    FindingIds=finding_ids[i:i+50]
                )
            )
            raw_findings.extend(response_i.get("Findings", []))

        normalized_findings: list[dict[str, Any]] = []
        for f in raw_findings:
            normalized_findings.append(self._normalize_finding(f, detector_id))

        return ToolResult(result=normalized_findings)

    @tracer.start_as_current_span("get_finding_details_async")
    async def get_finding_details_async(self, input: GetFindingDetailsInput) -> ToolResult:
        """
        Retrieves detailed information for a specific GuardDuty finding.

        :param input: GetFindingDetailsInput containing detector_id and finding_id
        :return: ToolResult where result is a dictionary of finding details
        """
        detector_id = input.detector_id
        finding_id = input.finding_id
        client = self._get_client()

        response = await asyncio.to_thread(
            lambda: client.get_findings(
                DetectorId=detector_id,
                FindingIds=[finding_id]
            )
        )
        raw_findings = response.get("Findings", []) or []
        if not raw_findings:
            return ToolResult(result={})

        return ToolResult(result=self._normalize_finding(raw_findings[0], detector_id))

    def _normalize_finding(self, finding: dict[str, Any], detector_id: str) -> dict[str, Any]:
        nf: dict[str, Any] = {}
        # id extraction
        if finding.get("Id"):
            nf["id"] = finding["Id"]
        else:
            arn_val = finding.get("Arn", "")
            parts = arn_val.split("/finding/")
            nf["id"] = parts[-1] if len(parts) > 1 else arn_val
        # mandatory fields
        nf.update({
            "arn": finding.get("Arn"),
            "type": finding.get("Type"),
            "detectorId": detector_id,
            "title": finding.get("Title"),
            "description": finding.get("Description"),
            "severity": finding.get("Severity"),
            "updatedAt": finding.get("UpdatedAt"),
            "createdAt": finding.get("CreatedAt"),
        })
        # optional fields
        if finding.get("AccountId") is not None:
            nf["accountId"] = finding.get("AccountId")
        if finding.get("Region") is not None:
            nf["region"] = finding.get("Region")
        if finding.get("Partition") is not None:
            nf["partition"] = finding.get("Partition")
        # resource normalization
        resource = finding.get("Resource")
        if isinstance(resource, dict):
            nf["resource"] = {k[0].lower() + k[1:]: v for k, v in resource.items()}
        # service details
        service = finding.get("Service")
        if isinstance(service, dict):
            nf["service"] = {k[0].lower() + k[1:]: v for k, v in service.items()}
        return nf
