# Final System Benchmark

`scripts/benchmark_final_system.py` measures the local FastAPI final research/demo runtime with one warmup request and five measured requests for health, readiness, model status, research evidence, ML inference, and DL inference. It records a first DL request separately and warm benign/malignant DL requests.

Run it from the project environment after the final artifacts are available:

```bash
PYTHONPATH=.:backend venv/bin/python scripts/benchmark_final_system.py
```

The generated [system_benchmark.json](../experiments/final/system_benchmark.json) and [system_benchmark.csv](../experiments/final/system_benchmark.csv) capture the operating-system, architecture, Python, TensorFlow, and scikit-learn versions used for that local run.

These values are local research/demo measurements, not a claim about universal production latency, capacity, or clinical suitability.
