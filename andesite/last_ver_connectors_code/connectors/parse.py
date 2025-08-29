
from string import Formatter
from typing import List, Union

from common.models.alerts import AlertDetailsLink, SummaryTableType
from connectors.config import AlertSummaryTableConfig


def split_text(value: str) -> list[str]:
    """
    Converts a block of text (delimited by carriage return and newline) to a list of strings
    """
    return [item.strip() for item in value.split("\r\n")]

def parse_texts_to_string(
    value: Union[str, list[str]], join_with: str = ", "
) -> str:
    """
    Converts a list of text to string
    """
    if not isinstance(value, list):
        value = [value]
    stripped_entries: list[str] = []
    for entry in value:
        stripped_entries.extend(split_text(entry))
    value = stripped_entries

    return join_with.join(str(v) for v in value)

def format_data_to_string(
    format_template: str,
    data: dict[str, Union[str, list[str]]],
    join_with: str = ", ",
) -> str:
    template_keys = [
        i[1] for i in Formatter().parse(format_template) if i[1] is not None
    ]

    # Format the string by replacing placeholders with corresponding values
    # If the key in the format template is not present in alert_details, this replaces it with an empty string
    # We cannot use .format() here as some of the keys may have periods in them (ex. annotations.mitre_attack)
    formatted_string = format_template
    for key in template_keys:
        formatted_string = formatted_string.replace(
            f"{{{key}}}",
            parse_texts_to_string(data.get(key, ""), join_with),
        )

    return formatted_string


def parse_summary_table(
    summary_table_configs: List[AlertSummaryTableConfig],
    alert_dict: dict[str, Union[str, list[str]]],
) -> SummaryTableType:
    summary_dict: SummaryTableType = dict()

    for config in summary_table_configs:
        config = AlertSummaryTableConfig.model_validate(config)
        if config.field_name in alert_dict:
            field_value = alert_dict.get(config.field_name)
            if not field_value:
                continue
            if config.link_format:
                field_value_as_list: list[str] = []
                if isinstance(field_value, list):
                    field_value_as_list = field_value
                else:
                    field_value_as_list = split_text(field_value)
                if config.link_replacements:
                    for pattern, replacement in config.link_replacements:
                        field_value_as_list = [
                            entry.replace(pattern, replacement)
                            for entry in field_value_as_list
                        ]
                summary_dict[config.friendly_name] = [  # type: ignore[index]
                    AlertDetailsLink(
                        display_text=entry,
                        link=config.link_format.format(entry),
                    )
                    for entry in field_value_as_list
                ]
            else:
                summary_dict[config.friendly_name] = parse_texts_to_string(  # type: ignore[index]
                    field_value
                )

    return summary_dict
