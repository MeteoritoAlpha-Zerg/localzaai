from common.models.mongo import DbDocument


class AlertAttributeDb(DbDocument):
    attribute_name: str
    mappings: dict[str, list[str]]
    context_weights: dict[str, float]
