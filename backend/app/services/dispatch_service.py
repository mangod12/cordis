async def select_responder(intent: str, severity: str) -> str:
    """Return responder category for MVP dispatch decisions.

    Covers every IntentType value:
        medical, fire, violent_crime, accident, gas_hazard,
        mental_health, non_emergency, unknown.

    Special responder types:
        hazmat          – chemical / gas incidents
        search_rescue   – earthquake / landslide scenarios
    """
    if severity == "critical":
        if intent == "fire":
            return "fire_dispatch"
        if intent == "gas_hazard":
            return "hazmat"
        if intent in {"medical", "mental_health", "accident"}:
            return "ambulance"
        if intent == "violent_crime":
            return "police_dispatch"
        # unknown / non_emergency at critical → police
        return "police_dispatch"

    if severity == "high":
        if intent in {"medical", "mental_health", "accident"}:
            return "ambulance"
        if intent == "fire":
            return "fire_dispatch"
        if intent == "gas_hazard":
            return "hazmat"
        if intent == "violent_crime":
            return "police_dispatch"
        return "police_dispatch"

    if severity == "medium":
        if intent == "medical":
            return "ambulance"
        if intent == "gas_hazard":
            return "hazmat"
        if intent == "fire":
            return "fire_dispatch"
        if intent == "violent_crime":
            return "police_dispatch"
        return "general_responder"

    # low severity
    if intent == "non_emergency":
        return "call_center_followup"
    return "call_center_followup"


# Keywords in transcript that indicate search-and-rescue is needed
_SEARCH_RESCUE_KW = frozenset([
    "earthquake", "landslide", "building collapse", "collapsed building",
    "people trapped", "bhookamp", "trapped under",
])


async def select_responder_with_context(
    intent: str, severity: str, transcript: str = ""
) -> str:
    """Enhanced dispatch that considers transcript keywords.

    Falls back to :func:`select_responder` but may override with
    *search_rescue* when earthquake / landslide keywords appear in
    the transcript at high or critical severity.
    """
    if severity in ("critical", "high") and transcript:
        lower = transcript.lower()
        if any(kw in lower for kw in _SEARCH_RESCUE_KW):
            return "search_rescue"
    return await select_responder(intent, severity)
