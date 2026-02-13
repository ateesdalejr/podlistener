"use client";

import { useEffect, useState } from "react";
import { Rss, Plus, Trash2, Loader2, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import type { Feed } from "@/types";
import { formatDistanceToNow } from "date-fns";

export default function FeedsPage() {
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const loadFeeds = () => {
    api.getFeeds().then(setFeeds).finally(() => setLoading(false));
  };

  useEffect(() => { loadFeeds(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    setAdding(true);
    setError("");
    try {
      await api.createFeed(url.trim());
      setUrl("");
      loadFeeds();
    } catch (err: any) {
      setError(err.message || "Failed to add feed");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this feed and all its episodes?")) return;
    await api.deleteFeed(id);
    loadFeeds();
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Feeds</h2>

      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste podcast RSS feed URL..."
          className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <button
          type="submit"
          disabled={adding}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
        >
          {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Add Feed
        </button>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : feeds.length === 0 ? (
        <div className="text-center p-12 text-gray-400">
          <Rss className="w-12 h-12 mx-auto mb-3" />
          <p>No feeds yet. Add a podcast RSS URL above.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {feeds.map((feed) => (
            <div
              key={feed.id}
              className="bg-white rounded-lg shadow-sm border p-4 flex items-center gap-4"
            >
              {feed.image_url ? (
                <img
                  src={feed.image_url}
                  alt=""
                  className="w-12 h-12 rounded-lg object-cover"
                />
              ) : (
                <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center">
                  <Rss className="w-5 h-5 text-gray-400" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h3 className="font-medium text-sm truncate">
                  {feed.title || feed.rss_url}
                </h3>
                <p className="text-xs text-gray-500 truncate">{feed.rss_url}</p>
                <div className="flex gap-3 mt-1 text-xs text-gray-400">
                  <span>{feed.episode_count} episodes</span>
                  {feed.last_polled_at && (
                    <span>
                      polled {formatDistanceToNow(new Date(feed.last_polled_at))} ago
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleDelete(feed.id)}
                className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                title="Delete feed"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
