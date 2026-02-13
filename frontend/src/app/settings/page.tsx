"use client";

import { FormEvent, useEffect, useState } from "react";
import { Loader2, Save } from "lucide-react";

import { api } from "@/lib/api";
import type { TranscriptionSettings } from "@/types";

export default function SettingsPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [provider, setProvider] = useState<"local" | "external">("local");
  const [externalUrl, setExternalUrl] = useState("");
  const [model, setModel] = useState("Systran/faster-whisper-small");
  const [apiKey, setApiKey] = useState("");
  const [clearApiKey, setClearApiKey] = useState(false);
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    api
      .getTranscriptionSettings()
      .then((settings: TranscriptionSettings) => {
        setProvider(settings.provider);
        setExternalUrl(settings.external_url);
        setModel(settings.model);
        setHasApiKey(settings.has_external_api_key);
      })
      .catch((err: Error) => setError(err.message || "Failed to load settings"))
      .finally(() => setLoading(false));
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError("");

    try {
      const payload: {
        provider: "local" | "external";
        external_url: string;
        model: string;
        external_api_key?: string;
        clear_external_api_key?: boolean;
      } = {
        provider,
        external_url: externalUrl,
        model,
      };

      if (apiKey.trim()) {
        payload.external_api_key = apiKey.trim();
      }
      if (clearApiKey) {
        payload.clear_external_api_key = true;
      }

      const result = await api.updateTranscriptionSettings(payload);
      setHasApiKey(result.has_external_api_key);
      setApiKey("");
      setClearApiKey(false);
      setSaved(true);
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">Settings</h2>

      <form onSubmit={onSubmit} className="bg-white rounded-lg shadow-sm border p-6 space-y-4">
        <h3 className="font-semibold">Transcription Provider</h3>

        <label className="block text-sm">
          <span className="text-gray-600">Provider</span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as "local" | "external")}
            className="mt-1 w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="local">Local Whisper Service</option>
            <option value="external">External API Service</option>
          </select>
        </label>

        <label className="block text-sm">
          <span className="text-gray-600">External API URL</span>
          <input
            type="url"
            value={externalUrl}
            onChange={(e) => setExternalUrl(e.target.value)}
            placeholder="https://api.openai.com/v1/audio/transcriptions"
            className="mt-1 w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </label>

        <label className="block text-sm">
          <span className="text-gray-600">Model</span>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="mt-1 w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </label>

        <label className="block text-sm">
          <span className="text-gray-600">External API Key</span>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={hasApiKey ? "Saved key exists. Enter a new key to replace it." : "Enter API key"}
            className="mt-1 w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </label>

        {hasApiKey && (
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={clearApiKey}
              onChange={(e) => setClearApiKey(e.target.checked)}
            />
            Clear saved API key
          </label>
        )}

        {error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}
        {saved && <div className="p-3 bg-green-50 text-green-700 rounded-lg text-sm">Saved</div>}

        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save
        </button>
      </form>
    </div>
  );
}
