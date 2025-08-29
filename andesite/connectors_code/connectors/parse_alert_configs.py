import re
from string import Formatter
from typing import Any, List

from common.models.alerts import AlertDetailsLink, AlertDetailsTable, SummaryTableType
from pydantic import BaseModel, model_validator

from connectors.config import AlertSummaryTableConfig


def split_text(value: str) -> list[str]:
    """
    Converts a block of text (delimited by carriage return and newline) to a list of strings
    """
    return [item.strip() for item in value.split("\r\n")]


def parse_texts_to_string(value: Any, join_with: str = ", ") -> str:
    """
    Converts a list of text to string
    """
    if not isinstance(value, list):
        value = [value]
    stripped_entries: list[str] = []
    for entry in value:
        stripped_entries.extend(split_text(str(entry)))
    value = stripped_entries

    return join_with.join(str(v) for v in value)


def format_data_to_string(
    outer_template: str,
    alert_details: AlertDetailsTable,
    join_with: str = ", ",
    inner_key_pattern: str | None = None,
) -> str:
    r"""
    Formats the data based on the provided format template and alert details.
    Args:
        format_template (str): The format template string.
        data (AlertDetailsTable): The alert details to be formatted.
        join_with (str): The string to join the values with.
        inner_key_pattern (str | None): Optional regex for formatting after format_template gets replaced.
    Returns:
        str: The formatted string.

    Example:
        format_template = "${rule_title}"
        data = AlertDetailsTable(rule_title={"$Computer$ ran net command $net_command$}, Computer="test_computer", net_command="net1")
        inner_key_pattern = r'\$(.*?)\$'

        formatted_string = format_data_to_string(format_template, data, join_with=", ", inner_key_pattern=inner_key_pattern)
        print(formatted_string) # Output: "test_computer ran net command net1"
    """
    template_keys = [i[1] for i in Formatter().parse(outer_template) if i[1] is not None]

    # Format the string by replacing placeholders with corresponding values
    # If the key in the format template is not present in alert_details, this replaces it with an empty string
    # We cannot use .format() here as some of the keys may have periods in them (ex. annotations.mitre_attack)
    formatted_string = outer_template
    for key in template_keys:
        formatted_string = formatted_string.replace(
            f"{{{key}}}",
            parse_texts_to_string(alert_details.get_field_value(key) or "", join_with),
        )
    if not inner_key_pattern:
        return formatted_string

    # If inner_key_pattern is provided, we will use it to replace the keys in the formatted string
    # with the corresponding values from the data
    # This is useful for cases where the formatted string has keys that are not present in the format template
    # For example, if the formatted string is "${rule_title} ran net command ${net_command}", we want to replace ${net_command} with the value of net_command
    # in the data
    # We will use the regex to find all the keys in the formatted string and replace them with the corresponding values from the data
    # The regex will match any key that is enclosed in ${} and replace it with the corresponding value from the data
    # If the key is not present in the data, we will leave it as is
    try:
        re.compile(inner_key_pattern)
    except re.error as e:
        raise ValueError(f"Invalid regex pattern for inner_key_pattern: {inner_key_pattern!r}. Error: {e}") from None

    def _replacer(match):
        key = match.group(1)
        return alert_details.get_field_value(key) or match.group(1)

    formatted_string = re.sub(inner_key_pattern, _replacer, formatted_string)
    return formatted_string


class DisplayTextAndFormattedText(BaseModel):
    display_text: str
    formatted_text: str = ""

    @model_validator(mode="before")
    def fill_formatted_text(cls, values):
        if "formatted_text" not in values or not values["formatted_text"]:
            values["formatted_text"] = values.get("display_text", "")
        return values


def parse_summary_table(
    summary_table_configs: List[AlertSummaryTableConfig],
    alert_details: AlertDetailsTable,
) -> SummaryTableType:
    """
    Parses the summary table based on the provided configurations and flattened alert dictionary.
    Args:
        summary_table_configs (List[AlertSummaryTableConfig]): List of configurations for the summary table.
        alert_details (AlertDetailsTable): The alert details to be parsed.
    Returns:
        SummaryTableType: Parsed summary table as a dictionary.
    """
    summary_dict: SummaryTableType = {}

    for config in summary_table_configs:
        field_value = alert_details.get_field_value(config.field_name)

        if not field_value:
            continue

        if config.link_format:
            if not isinstance(field_value, list):
                field_value = split_text(str(field_value))
            unique_values = list(dict.fromkeys(field_value))
            field_value_as_list = [DisplayTextAndFormattedText(display_text=entry) for entry in unique_values]
            if config.link_replacements:
                for pattern, replacement in config.link_replacements:
                    for entry in field_value_as_list:
                        entry.formatted_text = entry.formatted_text.replace(pattern, replacement)
            summary_dict[config.friendly_name] = [
                AlertDetailsLink(
                    display_text=entry.display_text,
                    link=config.link_format.format(entry.formatted_text),
                )
                for entry in field_value_as_list
            ]
        else:
            summary_dict[config.friendly_name] = parse_texts_to_string(  # type: ignore[index]
                field_value
            )

    return summary_dict
