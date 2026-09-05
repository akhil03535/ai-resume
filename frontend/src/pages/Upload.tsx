import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, FileText, Loader2, RefreshCw } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { ErrorState } from "@/components/States";
import { useToast } from "@/components/Toast";
import { uploadResume, parseResume } from "@/api/resumes";
import { apiErrorMessage } from "@/api/client";

type Stage = "idle" | "uploading" | "parsing" | "parse_failed" | "done";

export default function Upload() {
  const [stage, setStage] = useState<Stage>("idle");
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  // Kept across a failed parse so "Retry" re-parses this same uploaded
  // resume instead of silently discarding it and forcing a re-upload
  // (which would also create a duplicate Resume row for the same file).
  const [uploadedResumeId, setUploadedResumeId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { show } = useToast();

  const runParse = useCallback(async (resumeId: string) => {
    setStage("parsing");
    setError(null);
    try {
      await parseResume(resumeId);
      setStage("done");
      show("success", "Resume parsed successfully. Review your profile next.");
      navigate("/profile");
    } catch (err) {
      // The resume itself is safe - it was already uploaded and text was
      // extracted successfully. Only the AI parsing step failed, so we stay
      // on this screen with a Retry action rather than losing the upload.
      setError(apiErrorMessage(err));
      setStage("parse_failed");
    }
  }, [navigate, show]);

  const handleFile = useCallback(async (file: File) => {
    setError(null);
    setFileName(file.name);
    setUploadedResumeId(null);
    const ext = file.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setError("Please upload a PDF or DOCX file.");
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setError("File is too large. Maximum size is 8MB.");
      return;
    }

    try {
      setStage("uploading");
      const resume = await uploadResume(file);
      setUploadedResumeId(resume.id);
      await runParse(resume.id);
    } catch (err) {
      // Upload/extraction itself failed (bad file, corrupted, etc.) - here
      // there really is nothing to retry against, so this does go back to
      // the picker, same as before.
      setError(apiErrorMessage(err));
      setStage("idle");
    }
  }, [runParse]);

  const stageMessage: Record<Stage, string> = {
    idle: "",
    uploading: "Extracting resume...",
    parsing: "Analyzing your resume with AI...",
    parse_failed: "",
    done: "Done!",
  };

  return (
    <Layout>
      <PageHeader title="Upload Your Resume" subtitle="We'll extract your experience, skills, and education automatically." />

      <div className="card max-w-2xl">
        {stage === "idle" ? (
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              const file = e.dataTransfer.files?.[0];
              if (file) handleFile(file);
            }}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl py-14 px-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
              dragOver ? "border-primary-600 bg-primary-50" : "border-border hover:border-primary-300"
            }`}
          >
            <UploadCloud className="w-10 h-10 text-primary-900 mb-3" />
            <p className="font-medium text-ink">Drag & drop your resume here</p>
            <p className="text-sm text-ink-muted mt-1">or click to browse · PDF or DOCX, up to 8MB</p>
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </div>
        ) : stage === "parse_failed" ? (
          <div className="py-10 flex flex-col items-center justify-center text-center">
            <FileText className="w-8 h-8 text-ink-muted mb-3" />
            <p className="font-medium text-ink">{fileName}</p>
            <p className="text-sm text-ink-muted mt-1 mb-4">
              Your file was uploaded and its text was extracted successfully - only the AI parsing step failed.
              You don't need to upload it again.
            </p>
            {error && <div className="w-full mb-4"><ErrorState message={error} /></div>}
            <button
              className="btn-primary"
              onClick={() => uploadedResumeId && runParse(uploadedResumeId)}
            >
              <RefreshCw className="w-4 h-4" /> Retry parsing
            </button>
          </div>
        ) : (
          <div className="py-14 flex flex-col items-center justify-center text-center">
            <Loader2 className="w-8 h-8 text-primary-900 animate-spin mb-4" />
            <p className="font-medium text-ink flex items-center gap-2">
              <FileText className="w-4 h-4" /> {fileName}
            </p>
            <p className="text-sm text-ink-muted mt-1">{stageMessage[stage]}</p>
          </div>
        )}

        {stage === "idle" && error && <div className="mt-4"><ErrorState message={error} /></div>}
      </div>
    </Layout>
  );
}

