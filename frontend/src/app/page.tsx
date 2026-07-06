"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

const API = "http://localhost:8000";

export default function HomePage() {
  const router   = useRouter();
  const fileRef  = useRef<HTMLInputElement>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [dragging, setDragging] = useState(false);

  const startDemo = async () => {
    setLoading(true);
    setError("");
    try {
      const res  = await fetch(`${API}/api/pursuit/demo`, { method: "POST" });
      const data = await res.json();
      router.push(`/pursuit/${data.rfp_id}`);
    } catch {
      setError("Cannot reach the backend. Make sure the server is running on port 8000.");
      setLoading(false);
    }
  };

  const uploadFile = async (file: File) => {
    const name = file.name.toLowerCase();
    const validExts = [".pdf", ".docx", ".pptx", ".ppt"];
    if (!validExts.some(ext => name.endsWith(ext))) { setError("Please upload a PDF, DOCX, or PPTX file."); return; }
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("file", file);
    try {
      const res  = await fetch(`${API}/api/rfp/upload`, { method: "POST", body: form });
      const data = await res.json();
      router.push(`/pursuit/${data.rfp_id}`);
    } catch {
      setError("Upload failed. Make sure the server is running on port 8000.");
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) uploadFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) uploadFile(f);
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-16">

      {/* Top navigation */}
      <div className="fixed top-0 right-0 p-4 flex gap-3 z-50">
        <a href="/knowledge"
          className="px-4 py-2 bg-gray-800/80 backdrop-blur border border-gray-700 hover:border-purple-500 text-gray-300 hover:text-white text-sm rounded-lg transition-all">
          Knowledge Base
        </a>
      </div>

      <div className="mb-10 flex items-center gap-2 px-4 py-2 rounded-full border border-purple-800 bg-purple-950/40 text-purple-300 text-sm font-medium">
        <span className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
        HCLTech x OpenAI Agentic AI Hackathon — Track 2: Sales Operations
      </div>

      <div className="text-center mb-12 space-y-4 max-w-3xl">
        <h1 className="text-7xl font-black tracking-tight">
          <span className="text-white">Pursuit</span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">IQ</span>
        </h1>
        <p className="text-2xl text-gray-300 font-light">
          Agentic Pursuit Intelligence Platform
        </p>
      </div>

      <div className="w-full max-w-xl space-y-4">
        <button
          onClick={startDemo}
          disabled={loading}
          className="w-full py-5 rounded-2xl font-bold text-lg transition-all
                     bg-gradient-to-r from-purple-600 to-violet-600
                     hover:from-purple-500 hover:to-violet-500
                     text-white shadow-lg shadow-purple-900/40
                     disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center gap-3"
        >
          {loading ? (
            <>
              <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Starting pursuit...
            </>
          ) : (
            "Run Demo Pursuit — Nordbank AG Banking RFP"
          )}
        </button>

        <div className="flex items-center gap-4 text-gray-600">
          <div className="flex-1 h-px bg-gray-800" />
          <span className="text-sm">or upload your own RFP</span>
          <div className="flex-1 h-px bg-gray-800" />
        </div>

        <div
          onDrop={handleDrop}
          onDragOver={e => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onClick={() => fileRef.current?.click()}
          className={`w-full border-2 border-dashed rounded-2xl py-10 text-center cursor-pointer
                      transition-all select-none
                      ${dragging
                        ? "border-purple-400 bg-purple-900/20"
                        : "border-gray-700 hover:border-gray-500 bg-gray-900/30"
                      }`}
        >
          <p className="text-gray-300 font-medium">Drop your RFP here (PDF, DOCX, or PPTX)</p>
          <p className="text-gray-600 text-sm mt-1">or click to browse</p>
          <input ref={fileRef} type="file" accept=".pdf,.docx,.pptx,.ppt" className="hidden" onChange={handleFileChange} />
        </div>

        {error && (
          <div className="text-red-400 text-sm text-center bg-red-900/20 border border-red-800 rounded-xl py-3 px-4">
            {error}
          </div>
        )}
      </div>

      <div className="mt-16 max-w-3xl w-full">
        <p className="text-center text-gray-600 text-xs uppercase tracking-widest mb-6">
          The 6-Agent Pipeline
        </p>
        <div className="flex items-center justify-between gap-2">
          {[
            { n: 1, name: "RFP Decomposer",   color: "purple" },
            { n: 2, name: "Win Intelligence",  color: "blue"   },
            { n: 3, name: "Client Intel",      color: "cyan"   },
            { n: 4, name: "Competitor Shadow", color: "amber"  },
            { n: 5, name: "Pricing (o3)",      color: "green"  },
            { n: 6, name: "Draft Generator",   color: "pink"   },
          ].map((a, i) => (
            <div key={a.n} className="flex items-center flex-1">
              <div className="flex flex-col items-center gap-2 flex-1">
                <div className="w-10 h-10 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-sm font-bold text-gray-400">
                  {a.n}
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-400 leading-tight max-w-[70px] text-center">
                    {a.name}
                  </div>
                </div>
              </div>
              {i < 5 && (
                <div className="text-gray-700 text-lg mx-1">&rarr;</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
