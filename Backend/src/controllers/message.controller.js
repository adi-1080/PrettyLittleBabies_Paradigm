import { readFileSync, readdirSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = resolve(__dirname, "../../../data");

function loadAllChats() {
  const files = readdirSync(DATA_DIR).filter(
    (f) => f.startsWith("chat_") && f.endsWith(".json")
  );

  const allChats = [];
  for (const file of files) {
    const raw = readFileSync(resolve(DATA_DIR, file), "utf-8");
    allChats.push(JSON.parse(raw));
  }
  return allChats;
}

export const getUserForSidebar = (req, res) => {
  const chats = loadAllChats();
  const contacts = [];
  const seen = new Set();

  for (const chat of chats) {
    for (const p of chat.participants || []) {
      if (p.id !== "u1" && !seen.has(p.id)) {
        seen.add(p.id);
        contacts.push({
          _id: p.id,
          fullName: p.name,
          profilePicture: "",
          chatFile: chat.chat_id,
        });
      }
    }
  }

  return res.status(200).json(contacts);
};

export const getMessages = (req, res) => {
  const { id: contactId } = req.params;
  const chats = loadAllChats();

  // Find the chat that contains this contact
  let targetChat = null;
  for (const chat of chats) {
    if (chat.participants.some((p) => p.id === contactId)) {
      targetChat = chat;
      break;
    }
  }

  if (!targetChat) {
    return res.status(200).json([]);
  }

  const messages = (targetChat.messages || [])
    .filter((m) => m.content && m.content.trim().length > 0)
    .map((m) => ({
      _id: m.id,
      senderID: m.sender_id,
      receiverID: m.sender_id === "u1" ? contactId : "u1",
      text: m.content,
      createdAt: m.timestamp,
    }));

  return res.status(200).json(messages);
};
