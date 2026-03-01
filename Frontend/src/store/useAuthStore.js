import { create } from "zustand";
import { io } from "socket.io-client";

const BASE_URL = "http://localhost:5001";

export const useAuthStore = create((set, get) => ({
  // Hardcoded owner — no auth needed
  authUser: { _id: "u1", fullName: "Anupam" },
  isCheckingAuth: false,
  socket: null,
  onlineUsers: [],

  checkAuth: () => {
    // No-op, already authenticated
    get().connectSocket();
  },

  connectSocket: () => {
    const { authUser } = get();
    if (!authUser || get().socket?.connected) return;
    const socket = io(BASE_URL, {
      query: { userId: authUser._id },
    });
    socket.connect();
    set({ socket });

    socket.on("getOnlineUsers", (users) => {
      set({ onlineUsers: users });
    });
  },

  disconnectSocket: () => {
    if (get().socket?.connected) {
      get().socket.disconnect();
    }
  },
}));
