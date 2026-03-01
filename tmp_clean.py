import json

path = r"d:\Hackathons\paradigm 1.0\PrettyLittleBabies_Paradigm\data\chat_data.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

orig = len(data["messages"])
data["messages"] = [m for m in data["messages"] if m.get("content", "").strip()]
cleaned = len(data["messages"])

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Removed {orig - cleaned} empty messages ({orig} -> {cleaned})")
