import toast from "react-hot-toast";
import { create } from "zustand";
import { axiosInstance } from "../lib/axios";
import { useAuthStore } from "./useAuthStore";

export const useChatStore = create((set, get) => ({
  messages: [],
  users: [],
  selectedUser: null,
  isUsersLoading: false,
  isMessagesLoading: false,
  isSendingMessages: false,

  getUsers: async () => {
    set({ isUsersLoading: true });

    try {
      console.log("before request");
      const response = await axiosInstance.get("/messages/users");

      console.log(response);
      set({ users: response.data });
    } catch (error) {
      toast.error(error.response.data.message);
    } finally {
      set({ isUsersLoading: false });
    }
  },

  getMessages: async (userId) => {
    set({ isMessagesLoading: true });
    try {
      const response = await axiosInstance.get(`/messages/${userId}`);
      set({ messages: response.data });
    } catch (error) {
      toast.error(error.response.data.message);
    } finally {
      set({ isMessagesLoading: false });
    }
  },
  sendMessage: async (messageData) => {
    const { messages, selectedUser } = get();
    try {
      set({ isSendingMessages: true });
      const response = await axiosInstance.post(
        `/messages/send/${selectedUser._id}`,
        messageData
      );

      console.log(response);
      set(() => ({ messages: [...messages, response.data] }));
    } catch (error) {
      toast.error(error.response.data.message);
    } finally {
      set({ isSendingMessages: false });
    }
  },

  subscribeToMessages: () => {
    const { selectedUser } = get();
    if (!selectedUser) return;

    const socket = useAuthStore.getState().socket;

    socket.on("newMessage", (newMessage) => {
      if (newMessage.senderID !== selectedUser._id) return;
      set({ messages: [...get().messages, newMessage] });
    });
  },

  unsubscribeToMessages: () => {
    const socket = useAuthStore.getState().socket;
    socket.off("newMessage");
  },
  setSelectedUser: (selectUser) => set({ selectedUser: selectUser }),
}));
