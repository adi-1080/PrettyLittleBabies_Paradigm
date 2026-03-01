"""
Fix contact IDs across all chat JSON files so each contact has a unique ID.
Aakarshit = u2, Nishi Shah DJ = u3, svara Acm Women MPSTME = u4
"""
import json
from pathlib import Path

DATA_DIR = Path(r"d:\Hackathons\paradigm 1.0\PrettyLittleBabies_Paradigm\data")

CONTACT_ID_MAP = {
    "Aakarshit": "u2",
    "Nishi Shah DJ": "u3",
    "svara Acm Women MPSTME": "u4",
}

for json_file in DATA_DIR.glob("chat_*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    contact_name = None
    for p in data["participants"]:
        if p["id"] != "u1":
            contact_name = p["name"]
            break

    if contact_name and contact_name in CONTACT_ID_MAP:
        new_id = CONTACT_ID_MAP[contact_name]
        old_id = None

        # Update participant ID
        for p in data["participants"]:
            if p["name"] == contact_name:
                old_id = p["id"]
                p["id"] = new_id

        # Update message sender_ids
        if old_id:
            for msg in data["messages"]:
                if msg["sender_id"] == old_id:
                    msg["sender_id"] = new_id

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ {json_file.name}: {contact_name} → {new_id}")
    else:
        print(f"⏭️  {json_file.name}: no mapping for '{contact_name}'")
