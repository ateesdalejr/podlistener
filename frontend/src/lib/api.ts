import type {
  Feed,
  Episode,
  Keyword,
  Mention,
  DashboardStats,
  TranscriptionSettings,
  TranscriptionSettingsUpdate,
} from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Dashboard
  getStats: () => apiFetch<DashboardStats>("/api/v1/dashboard/stats"),

  // Settings
  getTranscriptionSettings: () =>
    apiFetch<TranscriptionSettings>("/api/v1/settings/transcription"),
  updateTranscriptionSettings: (payload: TranscriptionSettingsUpdate) =>
    apiFetch<TranscriptionSettings>("/api/v1/settings/transcription", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  // Feeds
  getFeeds: () => apiFetch<Feed[]>("/api/v1/feeds"),
  createFeed: (rss_url: string) =>
    apiFetch<Feed>("/api/v1/feeds", {
      method: "POST",
      body: JSON.stringify({ rss_url }),
    }),
  deleteFeed: (id: string) =>
    apiFetch<void>(`/api/v1/feeds/${id}`, { method: "DELETE" }),

  // Episodes
  getEpisodes: (feedId: string) =>
    apiFetch<Episode[]>(`/api/v1/episodes/by-feed/${feedId}`),
  getEpisode: (id: string) => apiFetch<Episode>(`/api/v1/episodes/${id}`),
  reprocessEpisode: (id: string) =>
    apiFetch<{ status: string }>(`/api/v1/episodes/${id}/reprocess`, {
      method: "POST",
    }),

  // Keywords
  getKeywords: () => apiFetch<Keyword[]>("/api/v1/keywords"),
  createKeyword: (phrase: string, match_type: string = "contains") =>
    apiFetch<Keyword>("/api/v1/keywords", {
      method: "POST",
      body: JSON.stringify({ phrase, match_type }),
    }),
  deleteKeyword: (id: string) =>
    apiFetch<void>(`/api/v1/keywords/${id}`, { method: "DELETE" }),

  // Mentions
  getMentions: (params?: Record<string, string>) => {
    const query = params
      ? "?" + new URLSearchParams(params).toString()
      : "";
    return apiFetch<Mention[]>(`/api/v1/mentions${query}`);
  },
  getMention: (id: string) => apiFetch<Mention>(`/api/v1/mentions/${id}`),
};
