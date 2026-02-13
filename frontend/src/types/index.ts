export interface Feed {
  id: string;
  rss_url: string;
  title: string | null;
  image_url: string | null;
  last_polled_at: string | null;
  created_at: string;
  episode_count: number;
}

export interface Episode {
  id: string;
  feed_id: string;
  guid: string;
  title: string | null;
  audio_url: string | null;
  published_at: string | null;
  status: string;
  created_at: string;
  mention_count: number;
  transcript_text?: string | null;
  error_message?: string | null;
}

export interface Keyword {
  id: string;
  phrase: string;
  match_type: string;
  created_at: string;
}

export interface Mention {
  id: string;
  episode_id: string;
  keyword_id: string;
  matched_text: string;
  transcript_segment: string;
  sentiment: string | null;
  sentiment_score: number | null;
  context_summary: string | null;
  topics: string[] | null;
  is_buying_signal: boolean | null;
  is_pain_point: boolean | null;
  is_recommendation: boolean | null;
  created_at: string;
  episode_title: string | null;
  podcast_title: string | null;
  keyword_phrase: string | null;
}

export interface DashboardStats {
  feeds: number;
  episodes: number;
  keywords: number;
  mentions: number;
  episodes_completed: number;
  episodes_processing: number;
  episodes_failed: number;
}

export interface TranscriptionSettings {
  provider: "local" | "external";
  external_url: string;
  model: string;
  has_external_api_key: boolean;
}

export interface TranscriptionSettingsUpdate {
  provider: "local" | "external";
  external_url: string;
  model: string;
  external_api_key?: string;
  clear_external_api_key?: boolean;
}
