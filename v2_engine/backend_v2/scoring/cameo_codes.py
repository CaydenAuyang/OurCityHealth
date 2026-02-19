"""
CAMEO (Conflict and Mediation Event Observations) event code lookup.

Mapping from numeric event codes to human-readable descriptions.
Used by the aggregator and evaluator to turn opaque GDELT EventCode values
into text the LLM can reason about and the end-user can understand.

Source: https://parusanalytics.com/eventdata/data.dir/cameo.html
"""

from __future__ import annotations

CAMEO_DESCRIPTIONS: dict[str, str] = {
    # ---- 01: Make Public Statement ----
    "010": "Make a public statement",
    "011": "Decline to comment",
    "012": "Make pessimistic comment",
    "013": "Make optimistic comment",
    "014": "Consider policy option",
    "015": "Acknowledge or claim responsibility",
    "016": "Deny responsibility",
    "017": "Engage in symbolic act",
    "018": "Make an empathetic comment",
    "019": "Express accord",
    # ---- 02: Appeal ----
    "020": "Make an appeal or request",
    # ---- 03: Cooperate ----
    "030": "Express intent to cooperate",
    # ---- 04: Consult ----
    "040": "Consult",
    # ---- 05: Diplomatic Cooperation ----
    "050": "Engage in diplomatic cooperation",
    # ---- 06: Material Cooperation ----
    "060": "Engage in material cooperation",
    # ---- 07: Aid ----
    "070": "Provide aid",
    # ---- 08: Yield ----
    "080": "Yield",
    # ---- 09: Investigate ----
    "090": "Investigate",
    # ---- 10: Demand ----
    "100": "Demand",
    # ---- 11: Disapprove ----
    "110": "Disapprove",
    # ---- 12: Reject ----
    "120": "Reject",
    # ---- 13: Threaten ----
    "130": "Threaten",
    "131": "Threaten non-force",
    "132": "Threaten with administrative sanctions",
    "133": "Threaten political dissent",
    "134": "Threaten to use military force",
    "135": "Threaten with weapons of mass destruction",
    "136": "Threaten to attack critical infrastructure",
    "137": "Threaten with violent repression",
    "138": "Threaten to impose economic sanctions",
    "139": "Give ultimatum",
    # ---- 14: Protest ----
    "140": "Protest",
    "141": "Demonstrate or rally",
    "142": "Conduct hunger strike",
    "143": "Conduct strike or boycott",
    "144": "Obstruct passage or block",
    "145": "Protest violently or riot",
    # ---- 15: Military Posture ----
    "150": "Exhibit military posture",
    "151": "Increase police alert status",
    "152": "Increase military alert status",
    "153": "Mobilize or increase armed forces",
    "154": "Fortify or build border structures",
    # ---- 16: Reduce Relations ----
    "160": "Reduce relations",
    "161": "Reduce or break diplomatic relations",
    "162": "Reduce or stop aid",
    "163": "Impose embargo, boycott, or sanctions",
    # ---- 17: Coerce ----
    "170": "Coerce",
    "171": "Seize or damage property",
    "172": "Impose administrative sanctions",
    "173": "Arrest, detain, or charge with legal action",
    "174": "Expel or deport individuals",
    "175": "Use tactics of violent repression",
    # ---- 18: Assault ----
    "180": "Assault",
    "181": "Abduct, hijack, or take hostage",
    "182": "Physically assault",
    "183": "Conduct suicide, car, or other non-military bombing",
    "184": "Use as human combatant",
    "185": "Attempt to assassinate",
    "186": "Assassinate",
    # ---- 19: Fight ----
    "190": "Fight",
    "191": "Engage in small arms fire",
    "192": "Engage in artillery fire",
    "193": "Conduct air or missile strike",
    "194": "Violate ceasefire",
    "195": "Employ aerial weapons",
    # ---- 20: Unconventional Mass Violence ----
    "200": "Engage in unconventional mass violence",
    "201": "Engage in mass expulsion",
    "202": "Engage in mass killings",
    "203": "Engage in ethnic cleansing",
    "204": "Use weapons of mass destruction",
}


def describe_event_code(code: str) -> str:
    """
    Return human description for a CAMEO code.

    Falls back to the root code (first two digits + "0") if the
    exact 3-digit code is not in the dictionary.
    """
    if not code:
        return "Unknown event"
    code = str(code).strip()
    if code in CAMEO_DESCRIPTIONS:
        return CAMEO_DESCRIPTIONS[code]
    root = code[:2] + "0"
    if root in CAMEO_DESCRIPTIONS:
        return CAMEO_DESCRIPTIONS[root]
    return "Event code " + code
