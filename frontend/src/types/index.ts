export interface DoctorProfile {
  doctor_id: string;
  doctor_email: string;
  doctor_name: string;
  specialty: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface MedicineCandidate {
  class_index: number;
  brand_name: string;
  generic_name: string;
  mapping_status: string;
  confidence: number;
}

export interface MedicineInfo {
  status: 'SUCCESS' | 'LOW_CONFIDENCE' | 'API_UNAVAILABLE';
  input_name: string;
  normalized_name: string;
  generic_name: string | null;
  rxcui: string | null;
  strength: string | null;
  dosage_form: string | null;
  match_confidence: number;
  indications: string[];
  warnings: string[];
  contraindications: string[];
  adverse_reactions: string[];
  drug_interactions: string[];
  source: {
    normalization: string;
    clinical_label: string;
  };
  requires_doctor_review: boolean;
  message?: string;
}

export interface LinePrediction {
  top_brand: string;
  generic_name: string | null;
  mapping_status: string;
  top_confidence: number;
  status: string;
  doctor_feedback_required: boolean;
  doctor_verification_required: boolean;
  review_priority: 'HIGH' | 'MEDIUM' | 'LOW';
  user_message: string;
  is_definitive_display: boolean;
  top_candidates: MedicineCandidate[];
  medicine_info?: MedicineInfo;
}

export interface MedicineLine {
  line_number: number;
  bounding_box: BoundingBox;
  segment_filename?: string;
  cropped_image_path?: string;
  prediction: LinePrediction;
  status?: 'PENDING' | 'CONFIRMED' | 'CORRECTED' | 'OOD';
  doctor_verified_label?: string;
}

export interface ReviewTask {
  review_id: string;
  prescription_id: string;
  image_reference: string;
  total_medicines_detected: number;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  status: 'PENDING' | 'CONFIRMED' | 'CORRECTED';
  original_prediction: string;
  original_confidence: number;
  prediction_status: string;
  model_version: string;
  created_at: string;
  all_medicines?: MedicineLine[];
  top_3_predictions?: MedicineCandidate[];
  doctor_verified_label?: string;
  doctor_action?: string;
  verification_timestamp?: string;
}

export interface FeedbackPayload {
  token: string;
  doctor_action: 'CONFIRM' | 'CORRECT';
  doctor_verified_label: string;
  doctor_id: string;
  doctor_email: string;
  line_number?: number;
  notes?: string;
}

export interface ModelVersion {
  version: string;
  status: 'LIVE' | 'CANDIDATE' | 'ARCHIVED';
  accuracy: number;
  deployed: boolean;
  created_at: string;
}

export interface AnalyticsSummary {
  confirmation_rate: number;
  correction_rate: number;
  ood_rate: number;
  total_reviews: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
}
