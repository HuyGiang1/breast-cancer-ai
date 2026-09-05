import { request } from '../core/api.js'; export const researchService={summary:()=>request('/research/summary/'),evidence:()=>request('/research/evidence/')};
