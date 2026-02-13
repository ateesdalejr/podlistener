"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { BarChart3, Rss, Search, MessageSquare, Loader2, AlertTriangle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { DashboardStats, Mention } from "@/types";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [mentions, setMentions] = useState<Mention[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getStats(), api.getMentions({ limit: "5" })])
      .then(([s, m]) => {
        setStats(s);
        setMentions(m);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  const cards = stats
    ? [
        { label: "Feeds", value: stats.feeds, icon: Rss, href: "/feeds" },
        { label: "Keywords", value: stats.keywords, icon: Search, href: "/keywords" },
        { label: "Mentions", value: stats.mentions, icon: MessageSquare, href: "/mentions" },
        { label: "Completed", value: stats.episodes_completed, icon: CheckCircle, color: "text-green-600" },
        { label: "Processing", value: stats.episodes_processing, icon: Loader2, color: "text-blue-600" },
        { label: "Failed", value: stats.episodes_failed, icon: AlertTriangle, color: "text-red-600" },
      ]
    : [];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {cards.map((card) => (
          <div key={card.label} className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">{card.label}</span>
              <card.icon className={`w-4 h-4 ${card.color || "text-gray-400"}`} />
            </div>
            <p className="text-2xl font-bold">
              {"href" in card ? (
                <Link href={card.href!} className="hover:text-blue-600">
                  {card.value}
                </Link>
              ) : (
                card.value
              )}
            </p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow-sm border">
        <div className="p-4 border-b">
          <h3 className="font-semibold flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Recent Mentions
          </h3>
        </div>
        {mentions.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No mentions yet. Add feeds and keywords to get started.
          </div>
        ) : (
          <div className="divide-y">
            {mentions.map((m) => (
              <div key={m.id} className="p-4">
                <div className="flex items-start justify-between mb-1">
                  <div>
                    <span className="text-sm font-medium">{m.keyword_phrase}</span>
                    <span className="mx-2 text-gray-300">in</span>
                    <span className="text-sm text-gray-600">{m.podcast_title}</span>
                  </div>
                  {m.sentiment && <SentimentBadge sentiment={m.sentiment} />}
                </div>
                <p className="text-sm text-gray-500 mb-1">{m.episode_title}</p>
                {m.context_summary && (
                  <p className="text-sm text-gray-700">{m.context_summary}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
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
