# SolidWorks Semantic Engine - Quick Start Guide

## Prerequisites

- Python 3.9+
- SolidWorks 2022+ (for add-in testing)
- Visual Studio 2022 (for C#/.NET add-in compilation)
- Ollama (https://ollama.ai)
- GPU recommended (NVIDIA with CUDA, or CPU fallback)

## Step 1: Setup Python Environment

```bash
cd C:\Users\JordanEhrig\Documents\GitHub\sw-semantic-engine

# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Test Parameterization Framework

```bash
cd parameterization

# Run parameter space example
python parameter_space.py

# Run parameter resolver example
python parameter_resolver.py
```

Expected output: C# code generated from parameter assignments.

## Step 3: Generate Training Data

```bash
cd training_pipeline

# Generate variations from mounting hole parameter space
python parameterization_data_generator.py
```

This creates `mounting_hole_training.json` with 32 training pairs.

## Step 4: Prepare Full Training Dataset

Once collectors/normalizers are implemented:

```bash
python run_pipeline.py --config config/training_full.yaml
```

This will:
1. Collect SolidWorks API docs
2. Collect GD&T standards
3. Normalize to structured format
4. Generate training variations
5. Export to Alpaca format
6. Ready for fine-tuning

## Step 5: Fine-tune Model

```bash
# Using Axolotl
axolotl train axolotl_solidworks_config.yml
```

Output: `./solidworks_finetune/` directory with LoRA weights.

## Step 6: Create GGUF Model for Ollama

```bash
# Convert to GGUF format
ollama create sw-semantic-7b --modelfile Modelfile
```

## Step 7: Start Backend Service

```bash
cd backend

# Start FastAPI
uvicorn main:app --reload --port 8000
```

API available at: http://localhost:8000

**Endpoints:**
- `POST /api/generate-code` - LLM code generation
- `GET /api/reference/{method}` - API documentation
- `POST /api/resolve-parameters` - Convert parameters to code

## Step 8: Build SolidWorks Add-in

```bash
# Open in Visual Studio
start addin/SolidWorksSemanticEngine.sln
```

1. Set reference path to SolidWorks PIAs (Primary Interop Assemblies)
2. Build (Release configuration)
3. Register as COM add-in
4. Restart SolidWorks

## Step 9: Test Integration

1. Open SolidWorks
2. Look for "SolidWorks Semantic Engine" in ribbon
3. Click "Generate Code" button
4. Enter a natural language prompt
5. View generated C# code

## Troubleshooting

### Ollama connection fails
```bash
# Start Ollama service
ollama serve

# In another terminal, test
ollama list
```

### Backend service won't start
```bash
# Check FastAPI installation
pip install -U fastapi uvicorn

# Check port availability
netstat -ano | findstr :8000
```

### SolidWorks add-in doesn't appear
```bash
# Register COM add-in manually
regasm addin\bin\Release\SolidWorksSemanticEngine.dll

# Verify
regedit → HKEY_LOCAL_MACHINE\SOFTWARE\SolidWorks\Addins\
```

## Project Structure Reference

```
sw-semantic-engine/
├── parameterization/          # Parameter space framework
│   ├── parameter_space.py     # Define parameters
│   └── parameter_resolver.py  # Convert to code
│
├── training_pipeline/         # Training data generation
│   ├── parameterization_data_generator.py
│   ├── collectors/            # Extract data sources
│   ├── normalizers/           # Structure data
│   └── generators/            # Create examples
│
├── backend/                   # FastAPI service
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   └── ollama_backend.py
│
├── addin/                     # C#/.NET add-in
│   ├── Commands/
│   ├── Bridge/
│   └── UI/
│
├── ARCHITECTURE.md            # Detailed design
├── requirements.txt
├── Modelfile                  # Ollama model definition
└── README.md
```

## Example: End-to-End Workflow

### 1. Define Parameter Space

```python
# In parameterization/parameter_space.py
FEATURE_X = ParameterSpace(
    name="feature_x",
    parameters={
        "depth": ParameterDefinition(...),
        "width": ParameterDefinition(...),
    }
)
```

### 2. Generate Training Data

```bash
cd training_pipeline
python parameterization_data_generator.py
```

### 3. Add to Training Pipeline

```bash
cat mounting_hole_training.json >> all_training_data.json
```

### 4. Fine-tune

```bash
axolotl train axolotl_solidworks_config.yml
```

### 5. Deploy

```bash
ollama create sw-semantic-7b --modelfile Modelfile
```

### 6. Use from Add-in

SolidWorks ribbon → "Generate Code" → "Create a hole with depth 10mm" → Generated C# code appears

## Next Steps

- [ ] Implement SolidWorks API collector
- [ ] Implement GD&T normalizer
- [ ] Build FastAPI endpoints
- [ ] Create C#/.NET add-in UI
- [ ] Generate 5000+ training pairs
- [ ] Fine-tune model
- [ ] Test end-to-end workflow
- [ ] Add MCP server for Claude integration

## Documentation

- `ARCHITECTURE.md` - Deep dive into design philosophy
- `README.md` - Project overview
- Code comments - Inline implementation details

## Support

For issues or questions:
1. Check ARCHITECTURE.md for design rationale
2. Review inline code comments
3. Check GitHub issues (when repo is pushed)
