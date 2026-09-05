import { useState } from "react";
import { X } from "lucide-react";
import { verifySkill } from "@/api/skills";
import { apiErrorMessage } from "@/api/client";
import { useToast } from "./Toast";
import type { MissingSkillPrompt } from "@/types";

type Step = "ask" | "where" | "describe";

const SOURCE_OPTIONS = [
  { value: "PROJECT", label: "Project" },
  { value: "INTERNSHIP", label: "Internship" },
  { value: "WORK", label: "Work" },
  { value: "COURSE", label: "Course" },
  { value: "OTHER", label: "Other" },
];

export default function SkillVerificationModal({
  prompts,
  onComplete,
}: {
  prompts: MissingSkillPrompt[];
  onComplete: () => void;
}) {
  const [index, setIndex] = useState(0);
  const [step, setStep] = useState<Step>("ask");
  const [sourceType, setSourceType] = useState("PROJECT");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { show } = useToast();

  const current = prompts[index];
  if (!current) return null;

  function advance() {
    setStep("ask");
    setSourceType("PROJECT");
    setDescription("");
    if (index + 1 < prompts.length) {
      setIndex(index + 1);
    } else {
      onComplete();
    }
  }

  async function handleAnswer(answer: "yes" | "basic" | "no") {
    if (answer === "yes") {
      setStep("where");
      return;
    }
    setSubmitting(true);
    try {
      await verifySkill({ skill_name: current.skill_name, answer });
      show("info", answer === "basic" ? `${current.skill_name} noted as basic knowledge.` : `${current.skill_name} will not appear in your resume.`);
      advance();
    } catch (e) {
      show("error", apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSubmitEvidence() {
    if (description.trim().length < 5) {
      show("error", "Please briefly describe how you used this skill.");
      return;
    }
    setSubmitting(true);
    try {
      await verifySkill({
        skill_name: current.skill_name,
        answer: "yes",
        evidence: [{ source_type: sourceType, description: description.trim() }],
      });
      show("success", `${current.skill_name} verified and available for your resume.`);
      advance();
    } catch (e) {
      show("error", apiErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/40" />
      <div className="relative bg-white w-full sm:max-w-md sm:rounded-card rounded-t-2xl p-6 animate-fade-in">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-medium text-ink-muted">
            Skill check {index + 1} of {prompts.length}
          </span>
          <button onClick={onComplete} aria-label="Close" className="p-1 text-ink-muted hover:text-ink">
            <X className="w-4 h-4" />
          </button>
        </div>

        {step === "ask" && (
          <>
            <h2 className="text-lg font-semibold text-ink mt-2">Do you know {current.skill_name}?</h2>
            <p className="text-sm text-ink-muted mt-1">
              This job description lists {current.skill_name} as a {current.requirement_importance === "REQUIRED" ? "required" : "preferred"} skill,
              but we didn't find it verified in your profile.
            </p>
            <div className="flex flex-col gap-2 mt-5">
              <button disabled={submitting} className="btn-primary justify-start" onClick={() => handleAnswer("yes")}>
                Yes, I've used it
              </button>
              <button disabled={submitting} className="btn-secondary justify-start" onClick={() => handleAnswer("basic")}>
                I have basic knowledge
              </button>
              <button disabled={submitting} className="btn-secondary justify-start" onClick={() => handleAnswer("no")}>
                No
              </button>
            </div>
          </>
        )}

        {step === "where" && (
          <>
            <h2 className="text-lg font-semibold text-ink mt-2">Where have you used {current.skill_name}?</h2>
            <div className="grid grid-cols-2 gap-2 mt-4">
              {SOURCE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSourceType(opt.value)}
                  className={
                    sourceType === opt.value
                      ? "btn-primary justify-center"
                      : "btn-secondary justify-center"
                  }
                >
                  {opt.label}
                </button>
              ))}
            </div>
            <button className="btn-primary w-full mt-5" onClick={() => setStep("describe")}>
              Continue
            </button>
          </>
        )}

        {step === "describe" && (
          <>
            <h2 className="text-lg font-semibold text-ink mt-2">Briefly describe how you used {current.skill_name}</h2>
            <textarea
              className="input mt-4 min-h-[100px] resize-none"
              placeholder="e.g. Used Kafka for event-driven communication between banking microservices."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={1000}
            />
            <p className="text-xs text-ink-muted mt-1">This becomes the evidence behind this skill on your tailored resume.</p>
            <button disabled={submitting} className="btn-primary w-full mt-4" onClick={handleSubmitEvidence}>
              {submitting ? "Saving..." : "Verify skill"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
