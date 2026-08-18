ALLOWED_TYPES = ["task", "grocery", "note", "reminder"]  

def validate_type(type: str) -> bool:
    if type not in ALLOWED_TYPES:
        raise ValueError(f"{type} not allowed")

    return True


def default_nag_policy(type: str) -> str:

    if type == "task":
        return "normal"
    elif type == "grocery":
        return "gental"
    else:
        return "off" 