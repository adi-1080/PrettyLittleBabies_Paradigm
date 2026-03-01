import express from "express";
import { getProfiles, getVerdicts, getActions, getOwner } from "../controllers/autopilot.controller.js";

const router = express.Router();

router.get("/profiles", getProfiles);
router.get("/verdicts", getVerdicts);
router.get("/actions", getActions);
router.get("/owner", getOwner);

export default router;
