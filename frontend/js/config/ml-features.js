export const ML_GROUPS = [
  ['Mean features', [
    'mean_radius', 'mean_texture', 'mean_perimeter', 'mean_area', 'mean_smoothness',
    'mean_compactness', 'mean_concavity', 'mean_concave_points', 'mean_symmetry', 'mean_fractal_dimension'
  ]],
  ['Standard error features', [
    'radius_error', 'texture_error', 'perimeter_error', 'area_error', 'smoothness_error',
    'compactness_error', 'concavity_error', 'concave_points_error', 'symmetry_error', 'fractal_dimension_error'
  ]],
  ['Worst features', [
    'worst_radius', 'worst_texture', 'worst_perimeter', 'worst_area', 'worst_smoothness',
    'worst_compactness', 'worst_concavity', 'worst_concave_points', 'worst_symmetry', 'worst_fractal_dimension'
  ]]
];

export const ML_FEATURES = ML_GROUPS.flatMap(([, features]) => features);

export const featureLabel = (key) =>
  key.split('_').map((x) => x[0].toUpperCase() + x.slice(1)).join(' ');

export const SAMPLES = {
  benign: {
    mean_radius: 13.54, mean_texture: 14.36, mean_perimeter: 87.46, mean_area: 566.3,
    mean_smoothness: 0.09779, mean_compactness: 0.08129, mean_concavity: 0.06664,
    mean_concave_points: 0.04781, mean_symmetry: 0.1885, mean_fractal_dimension: 0.05766,
    radius_error: 0.2699, texture_error: 0.7886, perimeter_error: 2.058, area_error: 23.56,
    smoothness_error: 0.008462, compactness_error: 0.0146, concavity_error: 0.02387,
    concave_points_error: 0.01315, symmetry_error: 0.0198, fractal_dimension_error: 0.0023,
    worst_radius: 15.11, worst_texture: 19.26, worst_perimeter: 99.7, worst_area: 711.2,
    worst_smoothness: 0.144, worst_compactness: 0.1773, worst_concavity: 0.239,
    worst_concave_points: 0.1288, worst_symmetry: 0.2977, worst_fractal_dimension: 0.07259,
  },
  malignant: {
    mean_radius: 17.99, mean_texture: 10.38, mean_perimeter: 122.8, mean_area: 1001.0,
    mean_smoothness: 0.1184, mean_compactness: 0.2776, mean_concavity: 0.3001,
    mean_concave_points: 0.1471, mean_symmetry: 0.2419, mean_fractal_dimension: 0.07871,
    radius_error: 1.095, texture_error: 0.9053, perimeter_error: 8.589, area_error: 153.4,
    smoothness_error: 0.006399, compactness_error: 0.04904, concavity_error: 0.05373,
    concave_points_error: 0.01587, symmetry_error: 0.03003, fractal_dimension_error: 0.006193,
    worst_radius: 25.38, worst_texture: 17.33, worst_perimeter: 184.6, worst_area: 2019.0,
    worst_smoothness: 0.1622, worst_compactness: 0.6656, worst_concavity: 0.7119,
    worst_concave_points: 0.2654, worst_symmetry: 0.4601, worst_fractal_dimension: 0.1189,
  },
};

export const GROUP_DESCRIPTIONS = {
  'Mean features': 'Average morphology measurements across fine needle aspirate (FNA) cell nuclei.',
  'Standard error features': 'Variability and estimation error of nuclear features across sampled cells.',
  'Worst features': 'Mean of the three largest (most severe) cell nuclei measurements per sample as defined in WDBC.',
};

export const WDBC_DEVELOPMENT_REFERENCE = {
  mean_radius: { min: 6.981, p01: 8.4091, p05: 9.5481, median: 13.34, p95: 20.593, p99: 24.9014, max: 28.11, mean: 14.1661, std: 3.5751, display_name: 'Mean Radius', group: 'Mean', description: 'Mean distance from center to points on cell nucleus perimeter.' },
  mean_texture: { min: 9.71, p01: 11.1236, p05: 13.114, median: 18.9, p95: 27.267, p99: 30.269, max: 39.28, mean: 19.4177, std: 4.2859, display_name: 'Mean Texture', group: 'Mean', description: 'Standard deviation of gray-scale values across the cell nucleus.' },
  mean_perimeter: { min: 43.79, p01: 53.8478, p05: 60.613, median: 86.18, p95: 137.38, p99: 168.638, max: 188.5, mean: 92.2159, std: 24.6899, display_name: 'Mean Perimeter', group: 'Mean', description: 'Mean perimeter length of the cell nucleus contour.' },
  mean_area: { min: 143.5, p01: 213.974, p05: 275.69, median: 546.7, p95: 1318.5, p99: 1889.34, max: 2501.0, mean: 657.8767, std: 356.1264, display_name: 'Mean Area', group: 'Mean', description: 'Mean area enclosed within the nuclear boundary.' },
  mean_smoothness: { min: 0.05263, p01: 0.07119, p05: 0.07897, median: 0.09578, p95: 0.11867, p99: 0.13328, max: 0.1634, mean: 0.0964, std: 0.0139, display_name: 'Mean Smoothness', group: 'Mean', description: 'Mean of local variation in radius lengths.' },
  mean_compactness: { min: 0.01938, p01: 0.03452, p05: 0.04751, median: 0.09362, p95: 0.20764, p99: 0.27909, max: 0.3454, mean: 0.1044, std: 0.0526, display_name: 'Mean Compactness', group: 'Mean', description: 'Perimeter^2 / area - 1.0 (mean across sampled nuclei).' },
  mean_concavity: { min: 0.0, p01: 0.0, p05: 0.00511, median: 0.06155, p95: 0.24523, p99: 0.35415, max: 0.4268, mean: 0.089, std: 0.0805, display_name: 'Mean Concavity', group: 'Mean', description: 'Mean severity of concave portions of the nucleus contour.' },
  mean_concave_points: { min: 0.0, p01: 0.0, p05: 0.00845, median: 0.03341, p95: 0.12457, p99: 0.16353, max: 0.2012, mean: 0.0489, std: 0.039, display_name: 'Mean Concave Points', group: 'Mean', description: 'Mean number of concave portions of the nucleus contour.' },
  mean_symmetry: { min: 0.106, p01: 0.13115, p05: 0.14777, median: 0.1794, p95: 0.22896, p99: 0.26252, max: 0.304, mean: 0.1813, std: 0.0275, display_name: 'Mean Symmetry', group: 'Mean', description: 'Mean nuclear symmetry across sampled nuclei.' },
  mean_fractal_dimension: { min: 0.04996, p01: 0.05191, p05: 0.05436, median: 0.06144, p95: 0.07548, p99: 0.0883, max: 0.09744, mean: 0.0628, std: 0.0071, display_name: 'Mean Fractal Dimension', group: 'Mean', description: 'Coastline approximation - 1 (mean across sampled nuclei).' },
  radius_error: { min: 0.1115, p01: 0.14923, p05: 0.17847, median: 0.3237, p95: 0.77197, p99: 1.29294, max: 2.873, mean: 0.4042, std: 0.279, display_name: 'Radius SE', group: 'Standard Error', description: 'Standard error of distance from center to points on perimeter.' },
  texture_error: { min: 0.3602, p01: 0.43577, p05: 0.5484, median: 1.11, p95: 2.2288, p99: 3.12328, max: 4.885, mean: 1.2227, std: 0.5614, display_name: 'Texture SE', group: 'Standard Error', description: 'Standard error of gray-scale values across the nucleus.' },
  perimeter_error: { min: 0.757, p01: 1.05389, p05: 1.2827, median: 2.287, p95: 5.6267, p99: 9.6806, max: 21.98, mean: 2.8647, std: 2.0522, display_name: 'Perimeter SE', group: 'Standard Error', description: 'Standard error of perimeter length for the nucleus.' },
  area_error: { min: 6.802, p01: 8.7618, p05: 11.458, median: 24.44, p95: 98.423, p99: 179.916, max: 542.2, mean: 40.3341, std: 46.1265, display_name: 'Area SE', group: 'Standard Error', description: 'Standard error of area enclosed within the nuclear boundary.' },
  smoothness_error: { min: 0.001713, p01: 0.003185, p05: 0.003998, median: 0.006351, p95: 0.012574, p99: 0.017772, max: 0.03113, mean: 0.007, std: 0.003, display_name: 'Smoothness SE', group: 'Standard Error', description: 'Standard error of local variation in radius lengths.' },
  compactness_error: { min: 0.002252, p01: 0.005728, p05: 0.008082, median: 0.02043, p95: 0.060132, p99: 0.093414, max: 0.1354, mean: 0.0254, std: 0.0181, display_name: 'Compactness SE', group: 'Standard Error', description: 'Standard error of perimeter^2 / area - 1.0.' },
  concavity_error: { min: 0.0, p01: 0.0, p05: 0.004838, median: 0.02592, p95: 0.07843, p99: 0.14728, max: 0.396, mean: 0.032, std: 0.0306, display_name: 'Concavity SE', group: 'Standard Error', description: 'Standard error of severity of contour concavities.' },
  concave_points_error: { min: 0.0, p01: 0.0, p05: 0.004488, median: 0.01093, p95: 0.022934, p99: 0.032128, max: 0.05279, mean: 0.0118, std: 0.0062, display_name: 'Concave Points SE', group: 'Standard Error', description: 'Standard error of number of contour concave portions.' },
  symmetry_error: { min: 0.007882, p01: 0.010574, p05: 0.012467, median: 0.01876, p95: 0.035414, p99: 0.046316, max: 0.07895, mean: 0.0205, std: 0.0083, display_name: 'Symmetry SE', group: 'Standard Error', description: 'Standard error of nuclear symmetry across sampled nuclei.' },
  fractal_dimension_error: { min: 0.000895, p01: 0.001258, p05: 0.001642, median: 0.003195, p95: 0.007901, p99: 0.012879, max: 0.02984, mean: 0.0038, std: 0.0027, display_name: 'Fractal Dimension SE', group: 'Standard Error', description: 'Standard error of coastline approximation - 1.' },
  worst_radius: { min: 7.93, p01: 9.2076, p05: 10.534, median: 14.97, p95: 25.682, p99: 30.7624, max: 36.04, mean: 16.2755, std: 4.8437, display_name: 'Worst Radius', group: 'Worst', description: 'Mean of the three largest nuclear radius values.' },
  worst_texture: { min: 12.02, p01: 15.2282, p05: 16.574, median: 25.44, p95: 36.438, p99: 41.8038, max: 49.54, mean: 25.6853, std: 6.1687, display_name: 'Worst Texture', group: 'Worst', description: 'Mean of the three largest nuclear texture values.' },
  worst_perimeter: { min: 50.41, p01: 58.87, p05: 67.854, median: 97.67, p95: 171.49, p99: 208.304, max: 251.2, mean: 107.2612, std: 33.6268, display_name: 'Worst Perimeter', group: 'Worst', description: 'Mean of the three largest nuclear perimeter values.' },
  worst_area: { min: 185.2, p01: 256.192, p05: 332.97, median: 686.5, p95: 2009.9, p99: 2918.14, max: 4254.0, mean: 880.6473, std: 570.0768, display_name: 'Worst Area', group: 'Worst', description: 'Mean of the three largest nuclear area values.' },
  worst_smoothness: { min: 0.07117, p01: 0.09062, p05: 0.10307, median: 0.1313, p95: 0.16982, p99: 0.18788, max: 0.2226, mean: 0.1324, std: 0.0229, display_name: 'Worst Smoothness', group: 'Worst', description: 'Mean of the three largest nuclear smoothness values.' },
  worst_compactness: { min: 0.02729, p01: 0.05436, p05: 0.08837, median: 0.2119, p95: 0.54848, p99: 0.77884, max: 1.058, mean: 0.2543, std: 0.1574, display_name: 'Worst Compactness', group: 'Worst', description: 'Mean of the three largest nuclear compactness values.' },
  worst_concavity: { min: 0.0, p01: 0.0, p05: 0.01836, median: 0.2267, p95: 0.6183, p99: 0.89984, max: 1.252, mean: 0.2723, std: 0.2087, display_name: 'Worst Concavity', group: 'Worst', description: 'Mean of the three largest nuclear concavity values.' },
  worst_concave_points: { min: 0.0, p01: 0.0, p05: 0.02821, median: 0.09993, p95: 0.23788, p99: 0.26875, max: 0.291, mean: 0.1146, std: 0.0657, display_name: 'Worst Concave Points', group: 'Worst', description: 'Mean of the three largest nuclear concave points values.' },
  worst_symmetry: { min: 0.1565, p01: 0.17725, p05: 0.21111, median: 0.2822, p95: 0.40426, p99: 0.49673, max: 0.6638, mean: 0.2901, std: 0.0619, display_name: 'Worst Symmetry', group: 'Worst', description: 'Mean of the three largest nuclear symmetry values.' },
  worst_fractal_dimension: { min: 0.05504, p01: 0.06037, p05: 0.06584, median: 0.08004, p95: 0.11909, p99: 0.14158, max: 0.2075, mean: 0.0839, std: 0.0181, display_name: 'Worst Fractal Dimension', group: 'Worst', description: 'Mean of the three largest nuclear fractal dimension values.' },
};
