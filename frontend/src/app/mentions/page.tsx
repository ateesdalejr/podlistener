"use client";

import { useEffect, useState } from "react";
import { MessageSquare, Loader2, TrendingUp, AlertCircle, ThumbsUp } from "lucide-react";
import { api } from "@/lib/api";
import type { Mention } from "@/types";
import { formatDistanceToNow } from "date-fns";

export default function MentionsPage() {
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    const params: Record<string, string> = {};
    if (filter) params.sentiment = filter;
    api.getMentions(params).then(setMentions).finally(() => setLoading(false));
  }, [filter]);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Mentions</h2>
        <div className="flex gap-1">
          {["", "positive", "negative", "neutral", "mixed"].map((s) => (
            <button
              key={s}
              onClick={() => { setLoading(true); setFilter(s); }}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === s
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {s || "All"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : mentions.length === 0 ? (
        <div className="text-center p-12 text-gray-400">
          <MessageSquare className="w-12 h-12 mx-auto mb-3" />
          <p>No mentions found. Mentions appear when keywords match podcast transcripts.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {mentions.map((m) => (
            <div key={m.id} className="bg-white rounded-lg shadow-sm border p-4">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <span className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded-full font-medium mr-2">
                    {m.keyword_phrase}
                  </span>
                  <span className="text-sm text-gray-500">
                    in <span className="font-medium text-gray-700">{m.podcast_title}</span>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {m.is_buying_signal && (
                    <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> Buying Signal
                    </span>
                  )}
                  {m.is_pain_point && (
                    <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" /> Pain Point
                    </span>
                  )}
                  {m.is_recommendation && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <ThumbsUp className="w-3 h-3" /> Recommendation
                    </span>
                  )}
                  {m.sentiment && <SentimentBadge sentiment={m.sentiment} />}
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-2">{m.episode_title}</p>

              {m.context_summary && (
                <p className="text-sm text-gray-800 mb-2">{m.context_summary}</p>
              )}

              <details className="text-xs text-gray-400">
                <summary className="cursor-pointer hover:text-gray-600">
                  View transcript segment
                </summary>
                <p className="mt-2 p-3 bg-gray-50 rounded text-gray-600 whitespace-pre-wrap">
                  {m.transcript_segment}
                </p>
              </details>

              <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                <span>{formatDistanceToNow(new Date(m.created_at))} ago</span>
                {m.topics && m.topics.length > 0 && (
                  <span>Topics: {m.topics.join(", ")}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const colors: Record<string, string> = {
    positive: "bg-green-100 text-green-700",
    negative: "bg-red-100 text-red-700",
    neutral: "bg-gray-100 text-gray-700",
    mixed: "bg-yellow-100 text-yellow-700",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${colors[sentiment] || colors.neutral}`}>
      {sentiment}
    </span>
  );
}
