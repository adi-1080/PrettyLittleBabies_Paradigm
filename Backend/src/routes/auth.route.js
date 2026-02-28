import express from "express";
import {
  signUp,
  login,
  logout,
  update,
  checkAuth,
} from "../controllers/auth.controller.js";
import { protectRoute } from "../middleware/auth.middleware.js";

const router = express.Router();

router.post("/signup", signUp);
router.post("/login", login);

router.put("/update", protectRoute, update);

router.post("/logout", logout); 

router.get("/check", protectRoute, checkAuth);

export default router;
