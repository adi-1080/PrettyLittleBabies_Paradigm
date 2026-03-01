import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const COLLECTIONS_DIR = resolve(__dirname, "../../../social-autopilot/collections");

function readCollection(filename) {
  const filePath = resolve(COLLECTIONS_DIR, filename);
  if (!existsSync(filePath)) return null;
  return JSON.parse(readFileSync(filePath, "utf-8"));
}

export const getProfiles = (req, res) => {
  const data = readCollection("historian_profiles.json");
  return res.status(200).json(data || []);
};

export const getVerdicts = (req, res) => {
  const data = readCollection("strategist_verdicts.json");
  return res.status(200).json(data || []);
};

export const getActions = (req, res) => {
  const data = readCollection("orchestrator_actions.json");
  return res.status(200).json(data || []);
};

export const getOwner = (req, res) => {
  const data = readCollection("owner_profile.json");
  return res.status(200).json(data || {});
};
