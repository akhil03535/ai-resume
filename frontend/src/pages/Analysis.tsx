import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Sparkles, RefreshCw } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import ScoreGauge from "@/components/ScoreGauge";
import CategoryRadar from "@/components/CategoryRadar";
import CoverageBarChart from "@/components/CoverageBarChart";
import SectionScoresChart from "@/components/SectionScoresChart";
import SkillBadge from "@/components/SkillBadge";
import SkillVerificationModal from "@/components/SkillVerificationModal";
import { LoadingState, ErrorState } from "@/components/States";
import { useToast } from "@/components/Toast";
import { getJobDescription, analyzeJobDescription } from "@/api/jobs";
import { runAnalysis, listAnalysesForJob } from "@/api/analysis";
import { getMissingSkills } from "@/api/skills";
import { apiErrorMessage } from "@/api/client";
import type { MissingSkillPrompt } from "@/types";

export default function Analysis() {
  const { jdId } = useParams<{ jdId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { show } = useToast();
  const [missingPrompts, setMissingPrompts] = useState<MissingSkillPrompt[] | null>(null);
  const [analyzingJd, setAnalyzingJd] = useState(false);

  const { data: jd, refetch: refetchJd } = useQuery({ queryKey: ["jd", jdId], queryFn: () => getJobDescription(jdId!), enabled: !!jdId });

  const { data: analyses, isLoading, error } = useQuery({
    queryKey: ["analyses", jdId],
    queryFn: () => listAnalysesForJob(jdId!),
    enabled: !!jdId && !!jd?.is_analyzed,
  });

  const latest = analyses?.[0];

  async function handleAnalyzeJd() {
    // Covers every path that can leave a JD un-analyzed - including a prior
    // analyze attempt that failed (e.g. AI unavailable) - without ever
    // re-creating the job description or losing what was already saved.
    setAnalyzingJd(true);
    try {
      show("info", "Extracting job requirements...");
      await analyzeJobDescription(jdId!);
      await refetchJd();
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      show("success", "Job description analyzed.");
    } catch (err) {
      show("error", apiErrorMessage(err));
    } finally {
      setAnalyzingJd(false);
    }
  }

  async function handleRunAnalysis() {
    try {
      show("info", "Comparing your profile...");
      const analysis = await runAnalysis({ job_description_id: jdId! });
      queryClient.invalidateQueries({ queryKey: ["analyses", jdId] });

      const prompts = await getMissingSkills(analysis.id);
      if (prompts.length > 0) {
        setMissingPrompts(prompts);
      } else {
        show("success", "Analysis complete.");
      }
    } catch (err) {
      show("error", apiErrorMessage(err));
    }
  }

  const matchedSkills = latest?.skill_matches.filter((s) => s.status === "MATCHED").length ?? 0;
  const partialSkills = latest?.skill_matches.filter((s) => s.status === "PARTIAL").length ?? 0;
  const missingSkills = latest?.skill_matches.filter((s) => s.status === "MISSING").length ?? 0;

  const matchedKw = latest?.keyword_matches.filter((k) => k.status === "MATCHED").length ?? 0;
  const partialKw = latest?.keyword_matches.filter((k) => k.status === "PARTIAL").length ?? 0;
  const missingKw = latest?.keyword_matches.filter((k) => k.status === "MISSING").length ?? 0;

  return (
    <Layout>
      <PageHeader
        title={jd?.title ?? "Analysis"}
        subtitle={jd?.company_name ?? undefined}
        actions={
          jd?.is_analyzed ? (
            <div className="flex gap-2">
              <button className="btn-secondary" onClick={handleRunAnalysis}>
                <RefreshCw className="w-4 h-4" /> {latest ? "Re-run analysis" : "Run analysis"}
              </button>
              {latest && (
                <button className="btn-primary" onClick={() => navigate(`/generator?jd=${jdId}`)}>
                  <Sparkles className="w-4 h-4" /> Generate Resume
                </button>
              )}
            </div>
          ) : undefined
        }
      />

      {!jd && <LoadingState message="Loading job description..." />}

      {jd && !jd.is_analyzed && (
        <div className="card text-center py-14">
          <p className="text-ink-muted mb-4">
            This job description hasn't been analyzed yet{jd.raw_text ? " - its requirements haven't been extracted" : ""}.
            Nothing has been lost; you can extract requirements now.
          </p>
          <button className="btn-primary mx-auto" onClick={handleAnalyzeJd} disabled={analyzingJd}>
            <Sparkles className="w-4 h-4" /> {analyzingJd ? "Analyzing..." : "Analyze job description"}
          </button>
        </div>
      )}

      {jd?.is_analyzed && isLoading && <LoadingState message="Loading analysis..." />}
      {jd?.is_analyzed && error && <ErrorState message={apiErrorMessage(error)} />}

      {jd?.is_analyzed && !isLoading && !latest && (
        <div className="card text-center py-14">
          <p className="text-ink-muted mb-4">No analysis yet for this job. Run one to see your ATS and job match scores.</p>
          <button className="btn-primary mx-auto" onClick={handleRunAnalysis}>
            <Sparkles className="w-4 h-4" /> Run analysis
          </button>
        </div>
      )}

      {latest && (
        <div className="space-y-6 animate-fade-in">
          <div className="card">
            <div className="flex flex-wrap items-center justify-around gap-6">
              <ScoreGauge score={latest.ats_score} label="ATS Score" />
              <div className="flex flex-col items-center">
                <div className="text-4xl font-bold text-primary-900">{latest.job_match_score}%</div>
                <span className="text-sm font-medium text-ink-muted mt-2">Job Match</span>
              </div>
              <ScoreGauge score={latest.completeness_score} label="Completeness" />
            </div>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <CategoryRadar categoryScores={latest.category_scores} />
            <div className="space-y-6">
              <CoverageBarChart title="Skill Match" matched={matchedSkills} partial={partialSkills} missing={missingSkills} />
              <CoverageBarChart title="Keyword Coverage" matched={matchedKw} partial={partialKw} missing={missingKw} />
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-4">Skill Gap Analysis</h2>
            <div className="flex flex-wrap gap-2">
              {latest.skill_matches.map((s, i) => (
                <SkillBadge key={i} label={s.skill_label} status={s.status} />
              ))}
            </div>
          </div>

          <div className="card">
            <h2 className="font-semibold mb-4">Keyword Analysis</h2>
            <div className="flex flex-wrap gap-2">
              {latest.keyword_matches.map((k, i) => (
                <SkillBadge key={i} label={k.keyword} status={k.status} />
              ))}
            </div>
          </div>

          <SectionScoresChart sectionScores={latest.section_scores} />

          <div className="card">
            <h2 className="font-semibold mb-4">AI Recommendations</h2>
            <div className="space-y-3">
              {["STRENGTH", "ISSUE", "SUGGESTION"].map((severity) => {
                const items = latest.recommendations.filter((r) => r.severity === severity);
                if (items.length === 0) return null;
                const heading = severity === "STRENGTH" ? "Strengths" : severity === "ISSUE" ? "Issues" : "Suggestions";
                const dotClass = severity === "STRENGTH" ? "bg-success" : severity === "ISSUE" ? "bg-danger" : "bg-warning";
                return (
                  <div key={severity}>
                    <h3 className="text-sm font-medium text-ink-muted mb-1.5">{heading}</h3>
                    <ul className="space-y-1.5">
                      {items.map((r, i) => (
                        <li key={i} className="text-sm flex items-start gap-2">
                          <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${dotClass}`} />
                          {r.text}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {missingPrompts && missingPrompts.length > 0 && (
        <SkillVerificationModal
          prompts={missingPrompts}
          onComplete={() => {
            setMissingPrompts(null);
            queryClient.invalidateQueries({ queryKey: ["analyses", jdId] });
            show("success", "Skill review complete. Re-run analysis to see updated results.");
          }}
        />
      )}
    </Layout>
  );
}
