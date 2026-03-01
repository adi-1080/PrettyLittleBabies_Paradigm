"""
Convert WhatsApp .txt exports to JSON format matching chat_data.json schema.
Maps both 'Aditya Gupta' and 'Anupam' to owner u1.
"""

import re
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(r"d:\Hackathons\paradigm 1.0\PrettyLittleBabies_Paradigm\data")

OWNER_NAMES = {"Aditya Gupta", "Anupam"}

# WhatsApp line pattern: DD/MM/YY, HH:MM - Sender: Message
LINE_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{2}),\s(\d{2}:\d{2})\s-\s(.+?):\s(.*)$"
)

SYSTEM_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{2}),\s(\d{2}:\d{2})\s-\s(?!.*:\s)(.*)$"
)


def parse_whatsapp(txt_path: Path) -> dict:
    lines = txt_path.read_text(encoding="utf-8").splitlines()

    messages = []
    participants_set = set()
    msg_id = 0
    current_msg = None

    for line in lines:
        match = LINE_RE.match(line)
        if match:
            # Flush previous message
            if current_msg:
                messages.append(current_msg)

            date_str, time_str, sender, content = match.groups()

            # Skip media omitted
            if content.strip() == "<Media omitted>":
                current_msg = None
                continue

            # Remove "<This message was edited>" suffix
            content = content.replace("<This message was edited>", "").strip()

            if not content:
                current_msg = None
                continue

            # Parse timestamp
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%y %H:%M")
                timestamp = dt.strftime("%Y-%m-%dT%H:%M:00Z")
            except ValueError:
                current_msg = None
                continue

            is_owner = sender in OWNER_NAMES
            sender_id = "u1" if is_owner else None
            sender_name = "Anupam" if is_owner else sender

            participants_set.add(sender_name)
            if sender_id is None:
                # Assign later
                pass

            msg_id += 1
            current_msg = {
                "id": f"m{msg_id}",
                "sender_id": sender_id,
                "sender_name": sender_name,
                "role": "user",
                "content": content,
                "timestamp": timestamp,
                "metadata": {},
                "_original_sender": sender,
            }
        elif SYSTEM_RE.match(line):
            # System message (encryption notice etc), skip
            if current_msg:
                messages.append(current_msg)
                current_msg = None
        else:
            # Continuation line — append to current message
            if current_msg and line.strip():
                current_msg["content"] += "\n" + line

    # Flush last
    if current_msg:
        messages.append(current_msg)

    # Determine contact name and assign IDs
    contact_names = [n for n in participants_set if n != "Anupam"]
    contact_name = contact_names[0] if contact_names else "Unknown"

    participants = [
        {"id": "u1", "name": "Anupam"},
        {"id": "u2", "name": contact_name},
    ]

    for msg in messages:
        if msg["sender_id"] is None:
            msg["sender_id"] = "u2"
        del msg["_original_sender"]

    # Filter empty content
    messages = [m for m in messages if m["content"].strip()]

    return {
        "chat_id": f"whatsapp_chat_{contact_name.lower().replace(' ', '_')}",
        "participants": participants,
        "messages": messages,
    }


def main():
    txt_files = [
        "WhatsApp Chat with Nishi Shah DJ.txt",
        "WhatsApp Chat with svara Acm Women MPSTME.txt",
    ]

    for txt_name in txt_files:
        txt_path = DATA_DIR / txt_name
        if not txt_path.exists():
            print(f"❌ Not found: {txt_name}")
            continue

        data = parse_whatsapp(txt_path)
        contact = data["participants"][1]["name"]
        out_name = f"chat_{contact.lower().replace(' ', '_')}.json"
        out_path = DATA_DIR / out_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ {txt_name}")
        print(f"   → {out_name} ({len(data['messages'])} messages, contact: {contact})")


if __name__ == "__main__":
    main()
