import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { processCertificates } from "@/integrations/extraction";
import { useState } from "react";
import { toast } from "sonner";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/contexts/AuthContext";

const Extract = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const { user } = useAuth();

  const generateHash = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const list = e.target.files ? Array.from(e.target.files) : [];
    setFiles(list);
  };

  const onProcess = async () => {
    if (!files.length) {
      toast("Please select at least one file.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const data = await processCertificates(files);
      setResult(data);
      toast.success("Processing complete");

      // If logged in, persist a minimal record to Supabase
      if (user) {
        try {
          const firstFile = files[0];
          const fileHash = firstFile ? await generateHash(firstFile) : null;
          const title = firstFile?.name || "Extracted Certificate";

          const { error } = await supabase.from("certificates").insert({
            user_id: user.id,
            title,
            status: "pending",
            file_hash: fileHash,
            ocr_data: data,
          } as any);

          if (error) {
            console.error("Supabase insert error:", error);
            toast.error("Saved locally, but failed to persist to Supabase");
          } else {
            toast.success("Saved to Supabase certificates");
          }
        } catch (e: any) {
          console.error("Supabase persist error:", e);
          // Non-blocking: keep UI result even if saving fails
        }
      }
    } catch (e: any) {
      toast.error(e?.message || "Failed to process files");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-semibold mb-4">Extract and Verify Certificates</h1>
        <p className="text-sm text-muted-foreground mb-6">
          Upload PDF or image files to run the extraction and verification pipeline.
        </p>

        <div className="flex items-center gap-4 mb-4">
          <input
            type="file"
            multiple
            accept=".pdf,image/*"
            onChange={onFileChange}
            className="border rounded p-2"
          />
          <button
            onClick={onProcess}
            disabled={loading}
            className="inline-flex items-center rounded bg-primary text-primary-foreground px-4 py-2 disabled:opacity-50"
          >
            {loading ? "Processing..." : "Process Certificates"}
          </button>
        </div>

        {result && (
          <div className="mt-6">
            <h2 className="text-xl font-medium mb-2">Result</h2>
            <pre className="bg-muted p-4 rounded overflow-auto max-h-[50vh] text-sm">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
};

export default Extract;