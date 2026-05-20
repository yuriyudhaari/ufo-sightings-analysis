"""
US state populations from 2010 Decennial Census.
Source: US Census Bureau. Public domain.
Used to compute per-capita UFO sighting rates.
2010 chosen as a midpoint of the heavy-reporting era (1998-2014).
"""

import pandas as pd

STATE_POP_2010 = {
    "al": 4779736, "ak": 710231, "az": 6392017, "ar": 2915918, "ca": 37253956,
    "co": 5029196, "ct": 3574097, "de": 897934, "fl": 18801310, "ga": 9687653,
    "hi": 1360301, "id": 1567582, "il": 12830632, "in": 6483802, "ia": 3046355,
    "ks": 2853118, "ky": 4339367, "la": 4533372, "me": 1328361, "md": 5773552,
    "ma": 6547629, "mi": 9883640, "mn": 5303925, "ms": 2967297, "mo": 5988927,
    "mt": 989415, "ne": 1826341, "nv": 2700551, "nh": 1316470, "nj": 8791894,
    "nm": 2059179, "ny": 19378102, "nc": 9535483, "nd": 672591, "oh": 11536504,
    "ok": 3751351, "or": 3831074, "pa": 12702379, "ri": 1052567, "sc": 4625364,
    "sd": 814180, "tn": 6346105, "tx": 25145561, "ut": 2763885, "vt": 625741,
    "va": 8001024, "wa": 6724540, "wv": 1852994, "wi": 5686986, "wy": 563626,
    "dc": 601723,
}

STATE_NAMES = {
    "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas",
    "ca": "California", "co": "Colorado", "ct": "Connecticut", "de": "Delaware",
    "fl": "Florida", "ga": "Georgia", "hi": "Hawaii", "id": "Idaho",
    "il": "Illinois", "in": "Indiana", "ia": "Iowa", "ks": "Kansas",
    "ky": "Kentucky", "la": "Louisiana", "me": "Maine", "md": "Maryland",
    "ma": "Massachusetts", "mi": "Michigan", "mn": "Minnesota",
    "ms": "Mississippi", "mo": "Missouri", "mt": "Montana", "ne": "Nebraska",
    "nv": "Nevada", "nh": "New Hampshire", "nj": "New Jersey",
    "nm": "New Mexico", "ny": "New York", "nc": "North Carolina",
    "nd": "North Dakota", "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon",
    "pa": "Pennsylvania", "ri": "Rhode Island", "sc": "South Carolina",
    "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas", "ut": "Utah",
    "vt": "Vermont", "va": "Virginia", "wa": "Washington",
    "wv": "West Virginia", "wi": "Wisconsin", "wy": "Wyoming",
    "dc": "District of Columbia",
}

if __name__ == "__main__":
    pop_df = pd.DataFrame([
        {"state_code": k.upper(), "state_name": STATE_NAMES[k], "population_2010": v}
        for k, v in STATE_POP_2010.items()
    ])
    pop_df.to_csv("state_populations.csv", index=False)
    print(f"Saved -> state_populations.csv ({len(pop_df)} rows)")