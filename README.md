# SolidWorks Semantic Engine (SWSE)

A comprehensive fine-tuned LLM system for SolidWorks API code generation, GD&T interpretation, sketch parameterization, and design intent capture.

**Core Domains:**
- SolidWorks COM API documentation
- Sketch constraints and dimensioning
- Geometric Dimensioning & Tolerancing (GD&T)
- Parameterization and design variability
- Feature-level design intent

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            SOLIDWORKS DESKTOP APPLICATION                   │
├─────────────────────────────────────────────────────────────┤
│  SolidWorks C#/.NET Add-in ←→ HTTP ←→ Python FastAPI        │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  FastAPI Backend (Port 8000)          │
        ├───────────────────────────────────────┤
        │  - SolidWorks API Reference           │
        │  - GD&T Interpreter                   │
        │  - Parameterization Engine            │
        │  - Ollama LLM Integration             │
        └───────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │  Ollama Local LLM                     │
        │  Fine-tuned Model: sw-semantic-7b    │
        └───────────────────────────────────────┘
```

## Project Structure

```
sw-semantic-engine/
├── training_pipeline/          # Data collection & model training
│   ├── collectors/
│   ├── normalizers/
│   ├── generators/
│   ├── parameterization/       # Parameter space exploration
│   ├── config/
│   └── run_pipeline.py
│
├── parameterization/           # Parameterization framework
│   ├── parameter_space.py
│   ├── parameter_store.py
│   ├── parameter_resolver.py
│   ├── templates/
│   └── examples/
│
├── backend/                    # FastAPI service
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   ├── services/
│   ├── ollama_backend.py
│   └── tests/
│
├── addin/                      # C#/.NET SolidWorks Add-in
│   ├── Application.cs
│   ├── Commands/
│   ├── Bridge/
│   ├── Models/
│   ├── UI/
│   └── Services/
│
├── docs/
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

1. **Setup environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   ```

2. **Run training pipeline:**
   ```bash
   cd training_pipeline
   python run_pipeline.py --config config/training_full.yaml
   ```

3. **Start backend service:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. **Build SolidWorks add-in:**
   Open `addin/SolidWorksSemanticEngine.sln` in Visual Studio 2022

## Training Data

Covers four primary domains:
- **SolidWorks API:** 500+ COM interface signatures
- **Sketch Constraints:** All constraint types and combinations
- **GD&T:** All 14 geometric characteristics per ASME Y14.5-2018
- **Parameterization:** Design parameter exploration and templates

## Parameterization Concept

The system understands SolidWorks parameters at multiple levels:

- **Sketch Parameters:** Dimensions with tolerances (length, angle, radius)
- **Feature Parameters:** Sketch selections, direction, depth, draft angle
- **Assembly Parameters:** Constraints, mating conditions, degrees of freedom
- **Design Parameters:** Named user variables, equations, design tables
- **GD&T Parameters:** Tolerance values, datum references, material modifiers
- **Design Intent Parameters:** Captured relationships and assumptions

## License

MIT
