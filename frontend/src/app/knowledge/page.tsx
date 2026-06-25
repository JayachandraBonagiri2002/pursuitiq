"use client";

import { useState, useEffect, useRef } from "react";

const API = "http://localhost:8000";

export default function KnowledgeBasePage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    industry: "",
    client_name: "",
    geography: "",
    deal_size: "",
    outcome: "WON",
    tags: "",
  });
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const res = await fetch(`${API}/api/knowledge/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch {
      // Knowledge base may not be connected yet
    }
  };

  const handleUpload = async (file: File) => {
    const valid = [".pdf", ".docx", ".pptx", ".ppt"];
    if (!valid.some(ext => file.name.toLowerCase().endsWith(ext))) {
      setMessage("Please upload a PDF, DOCX, or PPTX file.");
      return;
    }

    setUploading(true);
    setMessage("");
    const form = new FormData();
    form.append("file", file);
    form.append("industry", uploadForm.industry);
    form.append("client_name", uploadForm.client_name);
    form.append("geography", uploadForm.geography);
    form.append("deal_size", uploadForm.deal_size);
    form.append("outcome", uploadForm.outcome);
    form.append("tags", uploadForm.tags);

    try {
      const res = await fetch(`${API}/api/knowledge/upload`, { method: "POST", body: form });
      const data = await res.json();
      setMessage(`Uploaded: ${data.chunks_indexed} sections indexed from ${file.name}`);
      loadDocuments();
      setUploadForm({ industry: "", client_name: "", geography: "", deal_size: "", outcome: "WON", tags: "" });
    } catch {
      setMessage("Upload failed. Check server connection.");
    }
    setUploading(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`${API}/api/knowledge/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top: 8 }),
      });
      const data = await res.json();
      setSearchResults(data.results || []);
    } catch {
      setSearchResults([]);
    }
    setSearching(false);
  };

  return (
    <div className="min-h-screen px-6 py-8 max-w-5xl mx-auto">
      <a href="/" className="text-purple-400 text-sm hover:text-purple-300 mb-4 block">&larr; Back to pursuits</a>
      <h1 className="text-3xl font-bold text-white mb-2">Knowledge Base</h1>
      <p className="text-gray-400 mb-8">
        Upload winning proposals to make the AI smarter. Each document you add teaches the system
        your company&apos;s tone, pricing patterns, and proven strategies.
      </p>

      {/* Upload Section */}
      <div className="card mb-8">
        <h2 className="text-white font-semibold text-lg mb-4">Upload Proposal Document</h2>
        <p className="text-gray-500 text-sm mb-4">
          Supports PDF, DOCX, and PPTX. Add metadata to improve search relevance.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          <input
            placeholder="Industry (e.g. Banking)"
            value={uploadForm.industry}
            onChange={e => setUploadForm(f => ({...f, industry: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
          <input
            placeholder="Client name"
            value={uploadForm.client_name}
            onChange={e => setUploadForm(f => ({...f, client_name: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
          <input
            placeholder="Geography (e.g. Germany)"
            value={uploadForm.geography}
            onChange={e => setUploadForm(f => ({...f, geography: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
          <input
            placeholder="Deal size (e.g. $50M)"
            value={uploadForm.deal_size}
            onChange={e => setUploadForm(f => ({...f, deal_size: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
          <select
            value={uploadForm.outcome}
            onChange={e => setUploadForm(f => ({...f, outcome: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
          >
            <option value="WON">WON</option>
            <option value="LOST">LOST</option>
            <option value="PENDING">PENDING</option>
          </select>
          <input
            placeholder="Tags (comma-separated)"
            value={uploadForm.tags}
            onChange={e => setUploadForm(f => ({...f, tags: e.target.value}))}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
        </div>

        <div
          onClick={() => fileRef.current?.click()}
          onDrop={(e) => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f) handleUpload(f); }}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          className={`border-2 border-dashed rounded-xl py-8 text-center cursor-pointer transition-all
            ${dragging
              ? "border-purple-400 bg-purple-900/20"
              : "border-gray-700 hover:border-purple-500"
            }`}
        >
          {uploading ? (
            <div className="flex items-center justify-center gap-3">
              <span className="w-5 h-5 border-2 border-purple-400/30 border-t-purple-400 rounded-full animate-spin" />
              <span className="text-purple-300">Uploading and indexing...</span>
            </div>
          ) : (
            <>
              <p className="text-gray-300 font-medium">
                {dragging ? "Drop file to upload" : "Drop proposal here (PDF, DOCX, PPTX)"}
              </p>
              <p className="text-gray-600 text-sm mt-1">or click to browse</p>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.pptx,.ppt"
            className="hidden"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }}
          />
        </div>

        {message && (
          <p className={`mt-3 text-sm ${message.includes("fail") ? "text-red-400" : "text-green-400"}`}>
            {message}
          </p>
        )}
      </div>

      {/* Documents List */}
      <div className="card mb-8">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-white font-semibold text-lg">
            Indexed Documents ({documents.length})
          </h2>
          <button
            onClick={() => { fetch(`${API}/api/knowledge/reindex`, {method:"POST"}); setMessage("Re-indexing started..."); }}
            className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
          >
            Re-index All
          </button>
        </div>
        {documents.length === 0 ? (
          <p className="text-gray-600 text-sm py-4 text-center">
            No documents yet. Upload your first winning proposal above.
          </p>
        ) : (
          <div className="space-y-2">
            {documents.map((doc, i) => (
              <div key={i} className="flex items-center justify-between bg-gray-900/50 rounded-lg px-4 py-3">
                <div className="flex items-center gap-3">
                  <span className="text-purple-400 text-lg">
                    {doc.name.endsWith(".pdf") ? "P" : doc.name.endsWith(".pptx") ? "S" : "W"}
                  </span>
                  <div>
                    <p className="text-gray-200 text-sm font-medium">{doc.name}</p>
                    <p className="text-gray-600 text-xs">
                      {doc.metadata?.industry && `${doc.metadata.industry} · `}
                      {doc.metadata?.geography && `${doc.metadata.geography} · `}
                      {doc.metadata?.outcome || ""}
                      {doc.size_bytes && ` · ${(doc.size_bytes / 1024).toFixed(0)} KB`}
                    </p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded font-medium
                  ${doc.metadata?.outcome === "WON" ? "bg-green-900 text-green-300" :
                    doc.metadata?.outcome === "LOST" ? "bg-red-900 text-red-300" : "bg-gray-800 text-gray-400"}`}>
                  {doc.metadata?.outcome || "—"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Section */}
      <div className="card">
        <h2 className="text-white font-semibold text-lg mb-4">Search Knowledge Base</h2>
        <div className="flex gap-3 mb-4">
          <input
            placeholder="Search proposals... (e.g. 'banking cloud migration pricing')"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-500 focus:outline-none"
          />
          <button
            onClick={handleSearch}
            disabled={searching}
            className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {searching ? "..." : "Search"}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div className="space-y-3">
            {searchResults.map((r, i) => (
              <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-purple-400 font-medium">{r.section}</span>
                    <span className="text-gray-700">|</span>
                    <span className="text-xs text-gray-500">{r.filename}</span>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded
                    ${r.outcome === "WON" ? "bg-green-900/50 text-green-400" : "bg-gray-800 text-gray-500"}`}>
                    {r.outcome}
                  </span>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">
                  {r.content?.slice(0, 300)}{r.content?.length > 300 ? "..." : ""}
                </p>
                {(r.industry || r.geography) && (
                  <p className="text-gray-600 text-xs mt-2">
                    {r.industry && `${r.industry}`}{r.geography && ` · ${r.geography}`}{r.deal_size && ` · ${r.deal_size}`}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
