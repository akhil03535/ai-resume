import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, Trash2, X } from "lucide-react";
import Layout from "@/components/Layout";
import PageHeader from "@/components/PageHeader";
import { LoadingState, ErrorState } from "@/components/States";
import SkillBadge from "@/components/SkillBadge";
import { useToast } from "@/components/Toast";
import { getProfile, updateProfile } from "@/api/profile";
import { apiErrorMessage } from "@/api/client";
import type { Achievement, Certification, Education, Experience, ProjectItem } from "@/types";

export default function Profile() {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  const { show } = useToast();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [summary, setSummary] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [skillNames, setSkillNames] = useState<string[]>([]);
  const [newSkill, setNewSkill] = useState("");
  const [educations, setEducations] = useState<Education[]>([]);
  const [experiences, setExperiences] = useState<Experience[]>([]);
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [certifications, setCertifications] = useState<Certification[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!data) return;
    setFullName(data.full_name ?? "");
    setHeadline(data.headline ?? "");
    setSummary(data.summary ?? "");
    setEmail(data.email ?? "");
    setPhone(data.phone ?? "");
    setLocation(data.location ?? "");
    setSkillNames(data.candidate_skills.map((s) => s.skill_name));
    setEducations(data.educations);
    setExperiences(data.experiences);
    setProjects(data.projects);
    setCertifications(data.certifications);
    setAchievements(data.achievements);
  }, [data]);

  async function handleSave() {
    setSaving(true);
    try {
      await updateProfile({
        full_name: fullName,
        headline,
        summary,
        email,
        phone,
        location,
        educations,
        experiences,
        projects,
        certifications,
        achievements,
        skill_names: skillNames,
      });
      show("success", "Profile saved.");
      refetch();
    } catch (e) {
      show("error", apiErrorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  if (isLoading) return <Layout><LoadingState message="Loading your profile..." /></Layout>;
  if (error) return <Layout><ErrorState message={apiErrorMessage(error)} /></Layout>;

  return (
    <Layout>
      <PageHeader
        title="Candidate Profile"
        subtitle="Review and correct what we extracted from your resume before continuing."
        actions={
          <div className="flex gap-2">
            <button className="btn-primary" onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save changes"}
            </button>
            <button className="btn-secondary" onClick={() => navigate("/jobs")}>Next: Add Job →</button>
          </div>
        }
      />

      <div className="space-y-6">
        <section className="card">
          <h2 className="font-semibold mb-4">Personal Information</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="Full name" value={fullName} onChange={setFullName} />
            <Field label="Headline" value={headline} onChange={setHeadline} />
            <Field label="Email" value={email} onChange={setEmail} />
            <Field label="Phone" value={phone} onChange={setPhone} />
            <Field label="Location" value={location} onChange={setLocation} className="sm:col-span-2" />
          </div>
          <div className="mt-4">
            <label className="label">Summary</label>
            <textarea className="input min-h-[90px]" value={summary} onChange={(e) => setSummary(e.target.value)} />
          </div>
        </section>

        <section className="card">
          <h2 className="font-semibold mb-4">Skills</h2>
          {data && (
            <div className="flex flex-wrap gap-2 mb-4">
              {data.candidate_skills.map((s) => (
                <SkillBadge key={s.id} label={s.skill_name} status={s.verification_status} />
              ))}
            </div>
          )}
          <div className="flex flex-wrap gap-2 mb-3">
            {skillNames.map((s, i) => (
              <span key={i} className="badge-neutral">
                {s}
                <button onClick={() => setSkillNames(skillNames.filter((_, idx) => idx !== i))} aria-label={`Remove ${s}`}>
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              className="input"
              placeholder="Add a skill and press Enter"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && newSkill.trim()) {
                  e.preventDefault();
                  setSkillNames([...skillNames, newSkill.trim()]);
                  setNewSkill("");
                }
              }}
            />
            <button
              className="btn-secondary"
              onClick={() => {
                if (newSkill.trim()) {
                  setSkillNames([...skillNames, newSkill.trim()]);
                  setNewSkill("");
                }
              }}
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </section>

        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Experience</h2>
            <button
              className="btn-ghost"
              onClick={() => setExperiences([...experiences, { company: "", title: "", is_current: false, bullets: [], technologies: [] }])}
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          <div className="space-y-4">
            {experiences.map((exp, i) => (
              <div key={i} className="border border-border rounded-lg p-4">
                <div className="flex justify-between items-start gap-2">
                  <div className="grid sm:grid-cols-2 gap-3 flex-1">
                    <Field label="Title" value={exp.title} onChange={(v) => updateAt(experiences, setExperiences, i, { title: v })} />
                    <Field label="Company" value={exp.company} onChange={(v) => updateAt(experiences, setExperiences, i, { company: v })} />
                  </div>
                  <button className="text-danger p-1 mt-6" onClick={() => setExperiences(experiences.filter((_, idx) => idx !== i))} aria-label="Remove experience">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <label className="label mt-3">Bullets (one per line)</label>
                <textarea
                  className="input min-h-[80px]"
                  value={exp.bullets.join("\n")}
                  onChange={(e) => updateAt(experiences, setExperiences, i, { bullets: e.target.value.split("\n") })}
                />
              </div>
            ))}
            {experiences.length === 0 && <p className="text-sm text-ink-muted">No experience entries yet.</p>}
          </div>
        </section>

        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Projects</h2>
            <button className="btn-ghost" onClick={() => setProjects([...projects, { name: "", bullets: [], technologies: [] }])}>
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          <div className="space-y-4">
            {projects.map((p, i) => (
              <div key={i} className="border border-border rounded-lg p-4">
                <div className="flex justify-between items-start gap-2">
                  <Field label="Name" value={p.name} onChange={(v) => updateAt(projects, setProjects, i, { name: v })} className="flex-1" />
                  <button className="text-danger p-1 mt-6" onClick={() => setProjects(projects.filter((_, idx) => idx !== i))} aria-label="Remove project">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
                <label className="label mt-3">Bullets (one per line)</label>
                <textarea
                  className="input min-h-[70px]"
                  value={p.bullets.join("\n")}
                  onChange={(e) => updateAt(projects, setProjects, i, { bullets: e.target.value.split("\n") })}
                />
              </div>
            ))}
            {projects.length === 0 && <p className="text-sm text-ink-muted">No projects yet.</p>}
          </div>
        </section>

        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold">Education</h2>
            <button className="btn-ghost" onClick={() => setEducations([...educations, { institution: "" }])}>
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
          <div className="space-y-3">
            {educations.map((ed, i) => (
              <div key={i} className="grid sm:grid-cols-3 gap-3 border border-border rounded-lg p-4">
                <Field label="Institution" value={ed.institution} onChange={(v) => updateAt(educations, setEducations, i, { institution: v })} />
                <Field label="Degree" value={ed.degree ?? ""} onChange={(v) => updateAt(educations, setEducations, i, { degree: v })} />
                <Field label="Field of study" value={ed.field_of_study ?? ""} onChange={(v) => updateAt(educations, setEducations, i, { field_of_study: v })} />
              </div>
            ))}
            {educations.length === 0 && <p className="text-sm text-ink-muted">No education entries yet.</p>}
          </div>
        </section>
      </div>
    </Layout>
  );
}

function updateAt<T>(list: T[], setter: (v: T[]) => void, index: number, patch: Partial<T>) {
  const copy = [...list];
  copy[index] = { ...copy[index], ...patch };
  setter(copy);
}

function Field({
  label,
  value,
  onChange,
  className,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  className?: string;
}) {
  return (
    <div className={className}>
      <label className="label">{label}</label>
      <input className="input" value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}
