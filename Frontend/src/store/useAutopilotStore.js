import { create } from "zustand";
import { axiosInstance } from "../lib/axios";

export const useAutopilotStore = create((set) => ({
  profiles: [],
  verdicts: [],
  actions: [],
  ownerProfile: null,
  isLoading: false,

  fetchAll: async () => {
    set({ isLoading: true });
    try {
      const [profilesRes, verdictsRes, actionsRes, ownerRes] =
        await Promise.all([
          axiosInstance.get("/autopilot/profiles"),
          axiosInstance.get("/autopilot/verdicts"),
          axiosInstance.get("/autopilot/actions"),
          axiosInstance.get("/autopilot/owner"),
        ]);
      set({
        profiles: profilesRes.data,
        verdicts: verdictsRes.data,
        actions: actionsRes.data,
        ownerProfile: ownerRes.data,
      });
    } catch (error) {
      console.error("Failed to fetch autopilot data:", error);
    } finally {
      set({ isLoading: false });
    }
  },
}));
