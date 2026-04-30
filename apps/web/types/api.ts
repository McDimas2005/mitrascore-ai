export type Role = "UMKM_OWNER" | "FIELD_AGENT" | "ANALYST" | "ADMIN";

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: Role;
};

export type InstantCheck = {
  id: number;
  data_completeness_score: number;
  evidence_quality_score: number;
  detected_business_indicators: { indicators?: string[] };
  missing_data: string[];
  weak_evidence: string[];
  recommended_next_steps: string[];
  can_submit_to_analyst: boolean;
  ocr_summary: string;
  business_note_summary: string;
};

export type Review = {
  id: number;
  score: number;
  readiness_band: string;
  confidence_level: string;
  positive_signals: string[];
  red_flags: string[];
  main_reasons: string[];
  suggested_next_action: string;
  score_breakdown: Record<string, { weight: number; score: number; weighted: number }>;
  data_used: string[];
  data_not_used: string[];
  confidence_explanation: string;
  model_limitations: string[];
  analyst_notes: string;
  final_human_decision: string;
  final_human_decision_label: string;
  follow_up_actions: string[];
  reviewed_at?: string | null;
};

export type WorkflowStage = {
  code: string;
  label: string;
  summary: string;
};

export type EvidenceItem = {
  id: number;
  evidence_type: string;
  source_type: string;
  source_type_label: string;
  source_type_summary: string;
  source_type_effect: string;
  original_filename: string;
  storage_backend: string;
  storage_reference?: string;
  field_agent_note: string;
  ai_status: string;
  extraction_result?: {
    extracted_text: string;
    extracted_fields: Record<string, unknown>;
    detected_business_indicators: { indicators?: string[] };
    confidence_score: number;
    quality_flags: string[];
  };
};

export type RuntimeStatus = {
  ai_mode: "mock" | "azure";
  use_mock_ai: boolean;
  azure_vision_configured: boolean;
  azure_document_intelligence_configured: boolean;
  field_note_summary_mode: string;
  evidence_search_mode: string;
  storage_mode: "local" | "azure_blob";
  use_azure_blob_storage: boolean;
  azure_blob_configured: boolean;
  public_blob_urls_enabled: boolean;
  responsible_ai_notice: string;
};

export type VerificationReadiness = {
  approval_ready: boolean;
  policy_summary: string;
  verified_business_presence_count: number;
  required_verified_business_presence_count: number;
  verified_cashflow_count: number;
  required_verified_cashflow_count: number;
  verified_evidence_count: number;
  total_evidence_count: number;
  unverified_material_evidence: Array<{ id: number; filename: string; evidence_type: string; source_type: string }>;
  verified_without_notes: Array<{ id: number; filename: string; evidence_type: string }>;
  missing_requirements: string[];
  confidence_cap: string;
};

export type BorrowerProfile = {
  id: number;
  business_name: string;
  business_category: string;
  business_duration_months: number;
  financing_purpose: string;
  requested_amount: string;
  estimated_monthly_revenue: string;
  estimated_monthly_expense: string;
  simple_cashflow_note: string;
  business_note: string;
  status: string;
  status_label: string;
  workflow_stage: WorkflowStage;
  role_next_actions: Partial<Record<Role | "ADMIN", string[]>>;
  verification_readiness: VerificationReadiness;
  owner_detail?: User;
  assisted_by_detail?: User;
  consent?: { consent_given: boolean };
  latest_instant_check?: InstantCheck | null;
  latest_review?: Review | null;
  evidence_items?: EvidenceItem[];
  instant_checks?: InstantCheck[];
  reviews?: Review[];
  evidence_count?: number;
};
