import { request } from '../core/api.js';
const query=(values)=>{const p=new URLSearchParams();Object.entries(values).forEach(([k,v])=>{if(v!==undefined&&v!==null&&v!=='')p.set(k,String(v))});return p.size?`?${p}`:''};
export const predictionService={
  ml:(payload,{modelName,patientId}={})=>request(`/predict/${query({model_name:modelName,patient_id:patientId})}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}),
  dl:(file,{modelName,patientId,includeExplanation=false}={})=>{const body=new FormData();body.append('file',file);return request(`/predict/image/${query({model_name:modelName,patient_id:patientId,include_explanation:includeExplanation})}`,{method:'POST',body})},
  multimodal:({clinicalData,imageFile,mlModel,dlModel,patientId})=>{const body=new FormData();body.append('clinical_data',JSON.stringify(clinicalData));body.append('image_file',imageFile);if(mlModel)body.append('ml_model',mlModel);if(dlModel)body.append('dl_model',dlModel);if(patientId)body.append('patient_id',patientId);body.append('include_explanation','false');return request('/predict/multimodal/',{method:'POST',body})},
  history:(patientId)=>request(`/predictions/history/${query({patient_id:patientId})}`),
};
