from common.utils.pydantic_helper import CamelModel


class MitreEnterpriseTechnique(CamelModel):
    tid: str
    priority: int
    matrix_tactic: str
    stix_id: str
    name: str
    description: str
    url: str = ""
    created: str = ""
    last_modified: str = ""
    domain: str = ""
    version: str = ""
    tactics: str = ""
    detection: str = ""
    platforms: str = ""
    data_sources: str = ""
    is_sub_technique: str = ""
    sub_technique_of: str = ""
    defenses_bypassed: str = ""
    contributors: str = ""
    permissions_required: str = ""
    supports_remote: str = ""
    system_requirements: str = ""
    impact_type: str = ""
    effective_permissions: str = ""
    relationship_citations: str = ""

    def to_mongo(self):
        return self.model_dump()

    @staticmethod
    def from_mongo(document):
        if document is None:
            return None

        return MitreEnterpriseTechnique(**document)


class MitreEnterpriseTechniquePage(CamelModel):
    page: int
    page_size: int
    total_count: int
    results: list[MitreEnterpriseTechnique]


class MitreEnterpriseTechniqueUpdate(CamelModel):
    message: str
    matched_count: int | None = None
    modified_count: int | None = None
