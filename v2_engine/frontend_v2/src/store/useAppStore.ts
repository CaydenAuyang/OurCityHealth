import { create } from "zustand";

interface AppState {
  selectedCityId: string | null;
  selectedDate: string;
  selectedCityName: string | null;
  sidebarOpen: boolean;

  isPlaying: boolean;
  playbackSpeed: 1 | 2 | 5;

  apiOffline: boolean;
  showShortcuts: boolean;
  toastMessage: string | null;

  isCompareMode: boolean;
  comparedCityIds: string[];

  setSelectedCity: (id: string | null, name?: string | null) => void;
  setSelectedDate: (date: string) => void;
  toggleSidebar: () => void;
  setIsPlaying: (v: boolean) => void;
  setPlaybackSpeed: (v: 1 | 2 | 5) => void;
  setApiOffline: (v: boolean) => void;
  toggleShortcuts: () => void;
  showToast: (msg: string) => void;
  addToCompare: (id: string) => void;
  removeFromCompare: (id: string) => void;
  clearCompare: () => void;
  toggleCompareMode: () => void;
}

let _toastTimer: ReturnType<typeof setTimeout> | undefined;

export const useAppStore = create<AppState>((set, get) => ({
  selectedCityId: null,
  selectedCityName: null,
  selectedDate: "2024-01-15",
  sidebarOpen: true,
  isPlaying: false,
  playbackSpeed: 1,
  apiOffline: false,
  showShortcuts: false,
  toastMessage: null,
  isCompareMode: false,
  comparedCityIds: [],

  setSelectedCity: (id, name = null) =>
    set({ selectedCityId: id, selectedCityName: name, isPlaying: false }),

  setSelectedDate: (date) => set({ selectedDate: date }),

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setIsPlaying: (v) => set({ isPlaying: v }),

  setPlaybackSpeed: (v) => set({ playbackSpeed: v }),

  setApiOffline: (v) => set({ apiOffline: v }),

  toggleShortcuts: () => set((s) => ({ showShortcuts: !s.showShortcuts })),

  showToast: (msg) => {
    clearTimeout(_toastTimer);
    set({ toastMessage: msg });
    _toastTimer = setTimeout(() => set({ toastMessage: null }), 2000);
  },

  addToCompare: (id) => {
    const { comparedCityIds, showToast: toast } = get();
    if (comparedCityIds.includes(id)) return;
    if (comparedCityIds.length >= 3) {
      toast("Maximum 3 cities for comparison");
      return;
    }
    set({ comparedCityIds: [...comparedCityIds, id], isCompareMode: true });
  },

  removeFromCompare: (id) =>
    set((s) => {
      const next = s.comparedCityIds.filter((c) => c !== id);
      return {
        comparedCityIds: next,
        isCompareMode: next.length > 0 ? s.isCompareMode : false,
      };
    }),

  clearCompare: () => set({ comparedCityIds: [], isCompareMode: false }),

  toggleCompareMode: () =>
    set((s) => ({
      isCompareMode: !s.isCompareMode,
      comparedCityIds: !s.isCompareMode ? s.comparedCityIds : [],
    })),
}));
