import { request } from '../core/api.js';
const wdbc={samples:569,malignant:212,benign:357,features:30,development:455,test:114,seed:42};
const cbis={processedImages:2559,roiRepresentations:2559,manifestRows:5118,groups:2354,fullSplit:{train:1777,validation:390,test:392},groupSplit:{train:1648,validation:353,test:353},overlap:'0 / 0 / 0'};
export const researchService={summary:()=>request('/research/summary/'),evidence:()=>request('/research/evidence/'),async studies(){const evidence=await request('/research/evidence/');return{evidence,wdbc,cbis,ml:evidence.ml_metrics||[],dl:evidence.dl_metrics||[],calibration:evidence.calibration||{}}}};
