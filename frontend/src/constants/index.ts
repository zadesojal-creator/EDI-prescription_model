import { DoctorProfile, ReviewTask } from '../types';

export const CURRENT_DOCTOR: DoctorProfile = {
  doctor_id: "doc_001",
  doctor_email: "zadesojal@gmail.com",
  doctor_name: "Dr. Sojal Zade, M.D.",
  specialty: "Pediatrician / General Physician"
};

export const REGISTERED_BRANDS_78 = [
  { brand: "Ace", generic: "Paracetamol" },
  { brand: "Ace Plus", generic: "Paracetamol + Caffeine" },
  { brand: "Alatrol", generic: "Cetirizine Hydrochloride" },
  { brand: "Amocal", generic: "Amlodipine" },
  { brand: "Amodis", generic: "Metronidazole" },
  { brand: "Anzitor", generic: "Atorvastatin" },
  { brand: "Axodin", generic: "Fexofenadine Hydrochloride" },
  { brand: "Azithrocin", generic: "Azithromycin" },
  { brand: "Bextram", generic: "Multivitamin" },
  { brand: "Bizoran", generic: "Olmesartan + Amlodipine" },
  { brand: "Ceevit", generic: "Vitamin C (Ascorbic Acid)" },
  { brand: "Clofenac", generic: "Diclofenac Sodium" },
  { brand: "Covir", generic: "Remdesivir" },
  { brand: "De-Rash", generic: "Zinc Oxide" },
  { brand: "Delsartan", generic: "Losartan Potassium" },
  { brand: "Esonix", generic: "Esomeprazole" },
  { brand: "Fexo", generic: "Fexofenadine Hydrochloride" },
  { brand: "Filmet", generic: "Metronidazole" },
  { brand: "Finix", generic: "Rabeprazole Sodium" },
  { brand: "Fixim", generic: "Cefixime" },
  { brand: "Flamyd", generic: "Ibuprofen" },
  { brand: "Flexi", generic: "Cyclobenzaprine" },
  { brand: "Glimeran", generic: "Glimepiride" },
  { brand: "Indever", generic: "Propranolol" },
  { brand: "Ketocon", generic: "Ketoconazole" },
  { brand: "Keto A", generic: "Ketorolac Tromethamine" },
  { brand: "Losartan", generic: "Losartan Potassium" },
  { brand: "Maxpro", generic: "Esomeprazole" },
  { brand: "Monas", generic: "Montelukast" },
  { brand: "Napa", generic: "Paracetamol" },
  { brand: "Napa Extend", generic: "Paracetamol" },
  { brand: "Neocaten", generic: "Amlodipine" },
  { brand: "Omeprap", generic: "Omeprazole" },
  { brand: "Oral saline", generic: "Oral Rehydration Salts" },
  { brand: "Pantonix", generic: "Pantoprazole" },
  { brand: "Renova", generic: "Paracetamol" },
  { brand: "Rupa", generic: "Rupatadine" },
  { brand: "Seclo", generic: "Omeprazole" },
  { brand: "Sergel", generic: "Esomeprazole" },
  { brand: "Tufnil", generic: "Tolfenamic Acid" },
  { brand: "Viodin", generic: "Povidone-Iodine" },
  { brand: "Zimax", generic: "Azithromycin" }
];

export const MOCK_REVIEWS: ReviewTask[] = [
  {
    review_id: "rev_df6e53ddd5",
    prescription_id: "rx_81088bcc",
    image_reference: "/data/sample_prescription_multiline.png",
    total_medicines_detected: 5,
    priority: "HIGH",
    status: "PENDING",
    original_prediction: "Napa Extend",
    original_confidence: 0.938,
    prediction_status: "high_confidence",
    model_version: "v1.0",
    created_at: "2026-08-23T23:51:30+00:00",
    all_medicines: [
      {
        line_number: 1,
        bounding_box: { x: 44, y: 115, width: 716, height: 70 },
        prediction: {
          top_brand: "Unknown",
          generic_name: null,
          mapping_status: "UNVERIFIED",
          top_confidence: 0.531,
          status: "doctor_verification_required",
          doctor_feedback_required: true,
          doctor_verification_required: true,
          review_priority: "HIGH",
          user_message: "Low confidence prediction. Doctor review required.",
          is_definitive_display: false,
          top_candidates: [
            { class_index: 12, brand_name: "Cold er", generic_name: "Chlorpheniramine + Phenylephrine", mapping_status: "VERIFIED", confidence: 0.531 },
            { class_index: 54, brand_name: "Napa", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.221 },
            { class_index: 38, brand_name: "Seclo", generic_name: "Omeprazole", mapping_status: "VERIFIED", confidence: 0.110 }
          ]
        }
      },
      {
        line_number: 2,
        bounding_box: { x: 66, y: 180, width: 455, height: 67 },
        prediction: {
          top_brand: "Unknown",
          generic_name: null,
          mapping_status: "UNVERIFIED",
          top_confidence: 0.362,
          status: "doctor_verification_required",
          doctor_feedback_required: true,
          doctor_verification_required: true,
          review_priority: "HIGH",
          user_message: "Low confidence prediction. Doctor review required.",
          is_definitive_display: false,
          top_candidates: [
            { class_index: 15, brand_name: "Teyp", generic_name: "Paracetamol Syrup", mapping_status: "UNVERIFIED", confidence: 0.362 },
            { class_index: 0, brand_name: "Ace", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.284 },
            { class_index: 55, brand_name: "Napa Extend", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.155 }
          ]
        }
      },
      {
        line_number: 3,
        bounding_box: { x: 66, y: 243, width: 152, height: 54 },
        prediction: {
          top_brand: "Unknown",
          generic_name: null,
          mapping_status: "UNVERIFIED",
          top_confidence: 0.385,
          status: "doctor_verification_required",
          doctor_feedback_required: true,
          doctor_verification_required: true,
          review_priority: "HIGH",
          user_message: "Low confidence prediction.",
          is_definitive_display: false,
          top_candidates: [
            { class_index: 18, brand_name: "Ehli PD", generic_name: "Amoxicillin", mapping_status: "UNVERIFIED", confidence: 0.385 },
            { class_index: 7, brand_name: "Azithrocin", generic_name: "Azithromycin", mapping_status: "VERIFIED", confidence: 0.301 },
            { class_index: 41, brand_name: "Zimax", generic_name: "Azithromycin", mapping_status: "VERIFIED", confidence: 0.142 }
          ]
        }
      },
      {
        line_number: 4,
        bounding_box: { x: 177, y: 381, width: 380, height: 65 },
        prediction: {
          top_brand: "Napa Extend",
          generic_name: "Paracetamol",
          mapping_status: "VERIFIED",
          top_confidence: 0.938,
          status: "high_confidence",
          doctor_feedback_required: false,
          doctor_verification_required: false,
          review_priority: "LOW",
          user_message: "High confidence prediction.",
          is_definitive_display: true,
          top_candidates: [
            { class_index: 55, brand_name: "Napa Extend", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.938 },
            { class_index: 54, brand_name: "Napa", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.042 },
            { class_index: 0, brand_name: "Ace", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.012 }
          ]
        }
      },
      {
        line_number: 5,
        bounding_box: { x: 177, y: 534, width: 583, height: 94 },
        prediction: {
          top_brand: "Napa Extend",
          generic_name: "Paracetamol",
          mapping_status: "VERIFIED",
          top_confidence: 0.934,
          status: "high_confidence",
          doctor_feedback_required: false,
          doctor_verification_required: false,
          review_priority: "LOW",
          user_message: "High confidence prediction.",
          is_definitive_display: true,
          top_candidates: [
            { class_index: 55, brand_name: "Napa Extend", generic_name: "Paracetamol", mapping_status: "VERIFIED", confidence: 0.934 },
            { class_index: 38, brand_name: "Seclo", generic_name: "Omeprazole", mapping_status: "VERIFIED", confidence: 0.038 },
            { class_index: 15, brand_name: "Esonix", generic_name: "Esomeprazole", mapping_status: "VERIFIED", confidence: 0.015 }
          ]
        }
      }
    ]
  },
  {
    review_id: "rev_99a81b",
    prescription_id: "rx_90214a",
    image_reference: "/data/sample_prescription_multiline.png",
    total_medicines_detected: 3,
    priority: "MEDIUM",
    status: "PENDING",
    original_prediction: "Sergel",
    original_confidence: 0.784,
    prediction_status: "medium_confidence",
    model_version: "v1.0",
    created_at: "2026-08-23T22:15:10+00:00"
  },
  {
    review_id: "rev_33f42c",
    prescription_id: "rx_10928f",
    image_reference: "/data/sample_prescription_multiline.png",
    total_medicines_detected: 1,
    priority: "LOW",
    status: "PENDING",
    original_prediction: "Ace Plus",
    original_confidence: 0.962,
    prediction_status: "high_confidence",
    model_version: "v1.0",
    created_at: "2026-08-23T21:04:00+00:00"
  }
];
