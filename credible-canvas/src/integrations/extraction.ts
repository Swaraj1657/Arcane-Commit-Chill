const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export type ExtractionResult = any;

export async function processCertificates(files: File[]): Promise<ExtractionResult> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f, f.name));

  const res = await fetch(`${API_BASE}/process`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed with ${res.status}`);
  }

  return res.json();
}