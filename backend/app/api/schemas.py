from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PredictionRequest(BaseModel):
    # Mean features
    mean_radius: float = Field(..., description="Mean of distances from center to points on the perimeter")
    mean_texture: float = Field(..., description="Standard deviation of gray-scale values")
    mean_perimeter: float = Field(..., description="Mean size of the core tumor")
    mean_area: float = Field(..., description="Mean area of the core tumor")
    mean_smoothness: float = Field(..., description="Mean of local variation in radius lengths")
    mean_compactness: float = Field(..., description="Mean of perimeter^2 / area - 1.0")
    mean_concavity: float = Field(..., description="Mean of severity of concave portions of the contour")
    mean_concave_points: float = Field(..., description="Mean for number of concave portions of the contour")
    mean_symmetry: float = Field(..., description="Mean symmetry")
    mean_fractal_dimension: float = Field(..., description="Mean for 'coastline approximation' - 1")
    
    radius_error: float = Field(..., description="Standard error for the mean of distances from center to points on the perimeter")
    texture_error: float = Field(..., description="Standard error for standard deviation of gray-scale values")
    perimeter_error: float = Field(..., description="Standard error for the core tumor perimeter")
    area_error: float = Field(..., description="Standard error for the core tumor area")
    smoothness_error: float = Field(..., description="Standard error for local variation in radius lengths")
    compactness_error: float = Field(..., description="Standard error for perimeter^2 / area - 1.0")
    concavity_error: float = Field(..., description="Standard error for severity of concave portions of the contour")
    concave_points_error: float = Field(..., description="Standard error for number of concave portions of the contour")
    symmetry_error: float = Field(..., description="Standard error for symmetry")
    fractal_dimension_error: float = Field(..., description="Standard error for 'coastline approximation' - 1")

    worst_radius: float = Field(..., description="'Worst' or largest mean value for mean of distances from center to points on the perimeter")
    worst_texture: float = Field(..., description="'Worst' or largest mean value for standard deviation of gray-scale values")
    worst_perimeter: float = Field(..., description="'Worst' or largest mean value for core tumor perimeter")
    worst_area: float = Field(..., description="'Worst' or largest mean value for core tumor area")
    worst_smoothness: float = Field(..., description="'Worst' or largest mean value for local variation in radius lengths")
    worst_compactness: float = Field(..., description="'Worst' or largest mean value for perimeter^2 / area - 1.0")
    worst_concavity: float = Field(..., description="'Worst' or largest mean value for severity of concave portions of the contour")
    worst_concave_points: float = Field(..., description="'Worst' or largest mean value for number of concave portions of the contour")
    worst_symmetry: float = Field(..., description="'Worst' or largest mean value for symmetry")
    worst_fractal_dimension: float = Field(..., description="'Worst' or largest mean value for 'coastline approximation' - 1")

    class Config:
        json_schema_extra = {
            "example": {
                "mean_radius": 17.99, "mean_texture": 10.38, "mean_perimeter": 122.8,
                "mean_area": 1001.0, "mean_smoothness": 0.1184, "mean_compactness": 0.2776,
                "mean_concavity": 0.3001, "mean_concave_points": 0.1471, "mean_symmetry": 0.2419,
                "mean_fractal_dimension": 0.07871, "radius_error": 1.095, "texture_error": 0.9053,
                "perimeter_error": 8.589, "area_error": 153.4, "smoothness_error": 0.006399,
                "compactness_error": 0.04904, "concavity_error": 0.05373, "concave_points_error": 0.01587,
                "symmetry_error": 0.03003, "fractal_dimension_error": 0.006193, "worst_radius": 25.38,
                "worst_texture": 17.33, "worst_perimeter": 184.6, "worst_area": 2019.0,
                "worst_smoothness": 0.1622, "worst_compactness": 0.6656, "worst_concavity": 0.7119,
                "worst_concave_points": 0.2654, "worst_symmetry": 0.4601, "worst_fractal_dimension": 0.1189
            }
        }

class PredictionResponse(BaseModel):
    model_name: str
    prediction: int = Field(..., description="0 for Benign, 1 for Malignant")
    diagnosis: str = Field(..., description="'Benign' or 'Malignant'")
    probability: float = Field(..., description="Confidence probability of the prediction")
    raw_probability: Optional[float] = Field(None, description="Raw model probability before display calibration")
    calibration_mode: Optional[str] = Field(None, description="Probability calibration mode used for the displayed probability")
    risk_band: Optional[str] = Field(None, description="Low/Medium/High risk band based on calibrated malignant probability")
    analysis_text: Optional[str] = None
    advice: Optional[str] = None
    advice_provider: Optional[str] = None
    advice_model: Optional[str] = None
    explanation_image: Optional[str] = None
    top_features: Optional[List[Dict[str, Any]]] = None

class MultiModalResponse(BaseModel):
    ml_result: PredictionResponse
    dl_result: PredictionResponse
    combined_diagnosis: str
    combined_confidence: float
    combined_risk_band: Optional[str] = None
    advice: str
    advice_provider: Optional[str] = None
    advice_model: Optional[str] = None


class ClinicalExtractionResponse(BaseModel):
    values: Dict[str, Optional[float]]
    filled_count: int
    missing_fields: List[str]
    provider: str
    model: str
    raw_text: Optional[str] = None


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    role: str = Field("user", pattern="^(user|doctor)$")
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None
    expires_at: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class PatientCreateRequest(BaseModel):
    full_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    notes: Optional[str] = None


class PatientUpdateRequest(BaseModel):
    full_name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    notes: Optional[str] = None


class PatientResponse(PatientCreateRequest):
    id: int
    user_id: int
    created_at: str
    updated_at: str


class SavedPredictionResponse(BaseModel):
    id: int
    patient_id: Optional[int] = None
    prediction_type: str
    model_name: Optional[str] = None
    diagnosis: Optional[str] = None
    probability: Optional[float] = None
    raw_probability: Optional[float] = None
    calibration_mode: Optional[str] = None
    risk_band: Optional[str] = None
    advice: Optional[str] = None
    advice_provider: Optional[str] = None
    advice_model: Optional[str] = None
    created_at: str
    input_payload: Dict[str, Any]
    response_payload: Dict[str, Any]


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatTurn] = []


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    created_at: str


class SavedChatMessage(BaseModel):
    id: int
    question: str
    answer: str
    created_at: str
