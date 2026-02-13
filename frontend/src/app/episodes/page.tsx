"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FileText, Loader2, RefreshCw, Search as SearchIcon, Download, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import type { Episode, Feed } from "@/types";
import { format } from "date-fns";

type StatusFilter = "all" | "pending" | "downloading" | "transcribing" | "analyzing" | "completed" | "failed";

export default function EpisodesPage() {
  const searchParams = useSearchParams();
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [feedId, setFeedId] = useState<string>("");
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [detail, setDetail] = useState<Episode | null>(null);
  const [loadingFeeds, setLoadingFeeds] = useState(true);
  const [loadingEpisodes, setLoadingEpisodes] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getFeeds()
      .then((data) => {
        setFeeds(data);
        const requested = searchParams.get("feed");
        if (requested && data.some((f) => f.id === requested)) {
          setFeedId(requested);
        } else if (data.length > 0) {
          setFeedId(data[0].id);
        }
      })
      .catch((err: any) => setError(err.message || "Failed to load feeds"))
      .finally(() => setLoadingFeeds(false));
  }, [searchParams]);

  useEffect(() => {
    if (!feedId) return;
    setLoadingEpisodes(true);
    setSelectedId("");
    setDetail(null);
    api
      .getEpisodes(feedId)
      .then(setEpisodes)
      .catch((err: any) => setError(err.message || "Failed to load episodes"))
      .finally(() => setLoadingEpisodes(false));
  }, [feedId]);

  useEffect(() => {
    if (!selectedId) return;
    setLoadingDetail(true);
    api
      .getEpisode(selectedId)
      .then(setDetail)
      .catch((err: any) => setError(err.message || "Failed to load transcript"))
      .finally(() => setLoadingDetail(false));
  }, [selectedId]);

  const filteredEpisodes = useMemo(() => {
    const q = query.trim().toLowerCase();
    return episodes.filter((ep) => {
      const statusOk = statusFilter === "all" ? true : ep.status === statusFilter;
      const titleOk = q ? (ep.title || ep.guid).toLowerCase().includes(q) : true;
      return statusOk && titleOk;
    });
  }, [episodes, statusFilter, query]);

  const transcriptText = detail?.transcript_text || "";
  const wordCount = useMemo(() => {
    if (!transcriptText.trim()) return 0;
    return transcriptText.trim().split(/\s+/).length;
  }, [transcriptText]);

  const highlightedTranscript = useMemo(() => {
    const q = query.trim();
    if (!q) return [transcriptText];
    const parts = transcriptText.split(new RegExp(`(${escapeRegExp(q)})`, "ig"));
    return parts.map((part, idx) =>
      part.toLowerCase() === q.toLowerCase() ? (
        <mark key={idx} className="bg-yellow-200 rounded px-0.5">
          {part}
        </mark>
      ) : (
        <span key={idx}>{part}</span>
      ),
    );
  }, [transcriptText, query]);

  const handleReprocess = async () => {
    if (!detail?.id) return;
    if (!confirm("Reprocess this episode?")) return;
    try {
      await api.reprocessEpisode(detail.id);
      setDetail({ ...detail, status: "pending", error_message: null });
      setEpisodes((prev) =>
        prev.map((ep) => (ep.id === detail.id ? { ...ep, status: "pending" } : ep)),
      );
    } catch (err: any) {
      setError(err.message || "Failed to reprocess episode");
    }
  };

  const downloadTranscript = () => {
    if (!detail?.transcript_text) return;
    const blob = new Blob([detail.transcript_text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${(detail.title || detail.guid || "transcript").slice(0, 80)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Episodes & Transcripts
        </h2>
        <div className="flex items-center gap-2">
          <select
            value={feedId}
            onChange={(e) => setFeedId(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm bg-white"
            disabled={loadingFeeds || feeds.length === 0}
          >
            {feeds.length === 0 ? (
              <option value="">No feeds available</option>
            ) : (
              feeds.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.title || f.rss_url}
                </option>
              ))
            )}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
            className="px-3 py-2 border rounded-lg text-sm bg-white"
          >
            {["all", "pending", "downloading", "transcribing", "analyzing", "completed", "failed"].map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <div className="relative">
            <SearchIcon className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by title or highlight in transcript..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-8 pr-3 py-2 border rounded-lg text-sm w-64"
            />
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 bg-white rounded-lg border shadow-sm">
          <div className="p-3 border-b text-sm font-medium">Episodes</div>
          {loadingEpisodes ? (
            <div className="p-6 flex justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : filteredEpisodes.length === 0 ? (
            <div className="p-6 text-sm text-gray-400 text-center">
              {feeds.length === 0 ? "Add a feed to see episodes." : "No episodes match the filters."}
            </div>
          ) : (
            <div className="divide-y max-h-[70vh] overflow-auto">
              {filteredEpisodes.map((ep) => (
                <button
                  key={ep.id}
                  onClick={() => setSelectedId(ep.id)}
                  className={`w-full text-left p-3 hover:bg-gray-50 transition-colors ${
                    selectedId === ep.id ? "bg-gray-50" : ""
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium truncate">
                      {ep.title || ep.guid}
                    </p>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadgeClass(ep.status)}`}>
                      {ep.status}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
                    {ep.published_at && (
                      <span>{format(new Date(ep.published_at), "MMM d, yyyy")}</span>
                    )}
                    <span>{ep.mention_count} mentions</span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 bg-white rounded-lg border shadow-sm">
          <div className="p-3 border-b flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">
                {detail?.title || (detail ? detail.guid : "Select an episode")}
              </p>
              {detail && (
                <p className="text-xs text-gray-500">
                  {detail.status} • {wordCount} words
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleReprocess}
                disabled={!detail}
                className="px-3 py-1.5 text-xs border rounded-md hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                Reprocess
              </button>
              <button
                onClick={downloadTranscript}
                disabled={!detail?.transcript_text}
                className="px-3 py-1.5 text-xs border rounded-md hover:bg-gray-50 disabled:opacity-50 flex items-center gap-1"
              >
                <Download className="w-3 h-3" />
                Download
              </button>
            </div>
          </div>

          {loadingDetail ? (
            <div className="p-6 flex justify-center">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : !detail ? (
            <div className="p-6 text-sm text-gray-400 text-center">
              Pick an episode to view the transcript.
            </div>
          ) : detail.error_message ? (
            <div className="p-6 text-sm text-red-600">
              Transcript unavailable: {detail.error_message}
            </div>
          ) : detail.transcript_text ? (
            <div className="p-4 max-h-[70vh] overflow-auto">
              <div className="text-xs text-gray-500 mb-2">
                {detail.audio_url ? (
                  <a href={detail.audio_url} className="underline" target="_blank" rel="noreferrer">
                    Audio file
                  </a>
                ) : (
                  "Audio file not available"
                )}
              </div>
              <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                {highlightedTranscript}
              </div>
            </div>
          ) : (
            <div className="p-6 text-sm text-gray-400 text-center">
              Transcript not ready yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function statusBadgeClass(status: string) {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-700";
    case "failed":
      return "bg-red-100 text-red-700";
    case "transcribing":
    case "analyzing":
    case "downloading":
      return "bg-blue-100 text-blue-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
}
