import express from "express";
import dotenv from "dotenv";
import cookieParser from "cookie-parser";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";

import { app, server } from "./lib/socket.js";
import messageRoutes from "./routes/message.route.js";
import autopilotRoutes from "./routes/autopilot.route.js";

dotenv.config();

const PORT = process.env.PORT || 5001;

app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ limit: "50mb", extended: true }));
app.use(cookieParser());
app.use(
  cors({
    origin: "http://localhost:5173",
    credentials: true,
  })
);

app.use("/api/messages", messageRoutes);
app.use("/api/autopilot", autopilotRoutes);

server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
