export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface CandidateSkill {
  id: string;
  skill_name: string;
  proficiency: string | null;
  source: string;
  verification_status: "EXTRACTED" | "VERIFIED" | "BASIC" | "REJECTED";
}

export interface Education {
  id?: string;
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  gpa?: string | null;
}

export interface Experience {
  id?: string;
  company: string;
  title: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  bullets: string[];
  technologies: string[];
}

export interface ProjectItem {
  id?: string;
  name: string;
  description?: string | null;
  bullets: string[];
  technologies: string[];
  url?: string | null;
}

export interface Certification {
  id?: string;
  name: string;
  issuer?: string | null;
  issue_date?: string | null;
}

export interface Achievement {
  id?: string;
  title: string;
  description?: string | null;
}

export interface CandidateProfile {
  id: string;
  full_name: string | null;
  headline: string | null;
  summary: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  links: { label: string; url: string }[];
  educations: Education[];
  experiences: Experience[];
  projects: ProjectItem[];
  certifications: Certification[];
  achievements: Achievement[];
  candidate_skills: CandidateSkill[];
}

export interface ResumeFile {
  id: string;
  original_filename: string;
  file_type: string;
  status: "UPLOADED" | "PARSING" | "PARSED" | "FAILED";
  parse_error: string | null;
  created_at: string;
}

export interface JobRequirement {
  id: string;
  label: string;
  requirement_type: "SKILL" | "TECHNOLOGY" | "KEYWORD";
  importance: "REQUIRED" | "PREFERRED";
}

export interface JobDescription {
  id: string;
  title: string;
  company_name: string | null;
  raw_text: string;
  role_title: string | null;
  domain: string | null;
  experience_requirement: string | null;
  education_requirement: string | null;
  responsibilities: string[];
  is_analyzed: boolean;
  requirements: JobRequirement[];
  created_at: string;
}

export interface SkillMatch {
  skill_label: string;
  status: "MATCHED" | "PARTIAL" | "MISSING";
  similarity_score: number;
  is_verified: boolean;
}

export interface KeywordMatch {
  keyword: string;
  status: "MATCHED" | "PARTIAL" | "MISSING";
  occurrences: number;
}

export interface Recommendation {
  severity: "STRENGTH" | "ISSUE" | "SUGGESTION";
  text: string;
}

export interface ResumeAnalysis {
  id: string;
  job_description_id: string;
  ats_score: number;
  job_match_score: number;
  completeness_score: number;
  ats_components: Record<string, number>;
  category_scores: Record<string, number>;
  section_scores: Record<string, number>;
  skill_matches: SkillMatch[];
  keyword_matches: KeywordMatch[];
  recommendations: Recommendation[];
  created_at: string;
}

export interface MissingSkillPrompt {
  skill_name: string;
  requirement_importance: "REQUIRED" | "PREFERRED";
  job_requirement_id: string;
}

export interface GeneratedResume {
  id: string;
  version_name: string;
  template_slug: string;
  target_role: string | null;
  target_company: string | null;
  content: any;
  ats_score: number | null;
  job_match_score: number | null;
  source_ats_score: number | null;
  created_at: string;
}

export interface ResumeTemplate {
  slug: string;
  name: string;
  description: string;
  is_ats_safe: boolean;
}

export interface DashboardData {
  latest_ats_score: number | null;
  latest_job_match_score: number | null;
  resume_completeness: number;
  resume_count: number;
  generated_resume_count: number;
  recent_analyses: Array<{ id: string; ats_score: number; job_match_score: number; created_at: string }>;
  recent_generated_resumes: Array<{ id: string; version_name: string; ats_score: number | null; created_at: string }>;
  top_recommendations: Recommendation[];
}
