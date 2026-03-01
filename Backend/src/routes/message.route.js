import express from "express";
import { getUserForSidebar, getMessages } from "../controllers/message.controller.js";

const router = express.Router();

router.get("/users", getUserForSidebar);
router.get("/:id", getMessages);

export default router;
