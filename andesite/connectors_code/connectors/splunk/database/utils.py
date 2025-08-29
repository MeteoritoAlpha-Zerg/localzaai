from typing import List, Tuple


def change_authorization_token_type(frm: str, to: str, list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    headers = []
    for name, val in list:
        if name == "Authorization":
            headers.append((name, val.replace(frm, to)))
            continue
        headers.append((name, val))
    return headers
