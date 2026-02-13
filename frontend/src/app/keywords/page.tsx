"use client";

import { useEffect, useState } from "react";
import { Search, Plus, Trash2, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { Keyword } from "@/types";

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [loading, setLoading] = useState(true);
  const [phrase, setPhrase] = useState("");
  const [matchType, setMatchType] = useState("contains");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const loadKeywords = () => {
    api.getKeywords().then(setKeywords).finally(() => setLoading(false));
  };

  useEffect(() => { loadKeywords(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phrase.trim()) return;
    setAdding(true);
    setError("");
    try {
      await api.createKeyword(phrase.trim(), matchType);
      setPhrase("");
      loadKeywords();
    } catch (err: any) {
      setError(err.message || "Failed to add keyword");
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: string) => {
    await api.deleteKeyword(id);
    loadKeywords();
  };

  const matchTypeLabels: Record<string, string> = {
    contains: "Contains",
    exact_word: "Exact Word",
    regex: "Regex",
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Keywords</h2>

      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          type="text"
          value={phrase}
          onChange={(e) => setPhrase(e.target.value)}
          placeholder="Enter keyword or phrase..."
          className="flex-1 px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
        <select
          value={matchType}
          onChange={(e) => setMatchType(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="contains">Contains</option>
          <option value="exact_word">Exact Word</option>
          <option value="regex">Regex</option>
        </select>
        <button
          type="submit"
          disabled={adding}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-1"
        >
          {adding ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Add
        </button>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : keywords.length === 0 ? (
        <div className="text-center p-12 text-gray-400">
          <Search className="w-12 h-12 mx-auto mb-3" />
          <p>No keywords yet. Add keywords to watch for in podcasts.</p>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {keywords.map((kw) => (
            <div
              key={kw.id}
              className="bg-white rounded-lg shadow-sm border px-3 py-2 flex items-center gap-2 group"
            >
              <span className="text-sm font-medium">{kw.phrase}</span>
              <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                {matchTypeLabels[kw.match_type] || kw.match_type}
              </span>
              <button
                onClick={() => handleDelete(kw.id)}
                className="text-gray-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
