# SolidWorks Semantic Engine: Architecture

## Core Philosophy

**Design Intent First** - The system captures and reasons about design intent through parameterization, not just final geometry.

Three levels of understanding:
1. **Parameter Space** - What can vary and what are the constraints
2. **Parameter Assignment** - Concrete values for a specific design
3. **Executable Code** - C# code that implements the design

## System Components

### 1. Parameterization Framework (`parameterization/`)

**Core Files:**
- `parameter_space.py` - Define parameter types, domains, and constraints
- `parameter_resolver.py` - Convert parameter assignments to C# code
- `parameter_store.py` - Persistent storage of parameter spaces

**Key Concepts:**
- **ParameterType**: What kind of parameter (LENGTH, DIAMETER, TOLERANCE_VALUE, etc.)
- **ParameterDomain**: Which domain (SKETCH, FEATURE, GDT, ASSEMBLY, DESIGN_TABLE)
- **ParameterConstraint**: Value constraints (RANGE, DISCRETE, POSITIVE, EXPRESSED)
- **ParameterSpace**: Complete design intent definition
- **ParameterAssignment**: Concrete value assignment to a parameter space

**Why It Matters:**
```python
# Traditional approach (rigid)
"Create a hole with diameter 10mm at position (25, 15)"

# Parameterized approach (flexible, trainable)
HOLE_PARAMETERS = {
    "diameter": [5.0, 10.0, 15.0, 20.0],  # Can vary
    "x_position": [range(0, 100)],        # Can vary
    "y_position": [range(0, 100)],        # Can vary
    "tolerance": [0.05, 0.1, 0.2],       # Can vary
}
# Generate 4 x 100 x 100 x 3 = 120,000 training examples from one template!
```

### 2. Training Pipeline (`training_pipeline/`)

**Components:**
- `collectors/` - Extract SolidWorks API docs, GD&T standards, examples
- `normalizers/` - Standardize into structured format
- `generators/` - Create training examples
- `parameterization_data_generator.py` - **Generate variations from parameter spaces**

**Data Flow:**

```
SolidWorks API Docs  → Collect
GD&T Standards      ↓
Sketch Examples     Normalize
                    ↓
                Generate
                    ↓
           Parameter Space + Assignment
                    ↓
           Generate Variations (Cartesian product)
                    ↓
        Training Pairs (1000s from 1 template)
                    ↓
          Convert to Alpaca Format
                    ↓
         Fine-tune with Axolotl
                    ↓
        GGUF Model for Ollama
```

**Why Parameterization in Training:**

Traditionally, training a model on sketches requires:
- 1000 hand-annotated examples
- Manual curation
- Coverage gaps

With parameterization:
- 1 parameter space definition
- Auto-generate 1000+ variations
- Perfect coverage of design space
- Model learns relationships between parameters

### 3. Backend Service (`backend/`)

**FastAPI Architecture:**

```python
# Lifespan management (Rev-Suite pattern)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    - Load fine-tuned model into Ollama
    - Initialize parameter space registry
    - Load training data index
    yield
    # Shutdown

# Dependency injection
def get_interpreter() -> BCLInterpreter:
    """Cached interpreter instance."""
    return _interpreter
```

**Endpoints:**
- `POST /api/generate-code` - LLM-powered code generation
- `GET /api/reference/{method}` - API documentation lookup
- `POST /api/validate-code` - Validate generated C# code
- `POST /api/parameter-space/{name}` - Get parameter space definition
- `POST /api/resolve-parameters` - Convert parameters to code

### 4. SolidWorks Add-in (`addin/`)

**C#/.NET Architecture (Rev-Suite pattern):**

```csharp
// COM add-in interface
public class SwAddin : ISwAddin
{
    // Ribbon commands
    Commands/
    ├── GenerateCodeCommand.cs    // LLM code generation
    ├── ParametrizeCommand.cs     // Set up parameter space
    └── ExplainCommand.cs         // API reference lookup

    // HTTP bridge to Python backend
    Bridge/
    └── ApiClient.cs

    // UI components
    UI/
    ├── CodeGeneratorPanel.cs
    └── ParameterPanel.cs

    // Services
    Services/
    ├── SolidWorksContextService.cs
    └── ParameterService.cs
}
```

## Training Data Strategy

### Phase 1: SolidWorks API
- Source: Official documentation + PIA metadata
- Focus: COM interface signatures, parameters, return types
- Output: 500+ API usage patterns
- Training: "Write code to [API goal]" → C# implementation

### Phase 2: Sketch Constraints
- Source: SolidWorks constraint types, examples
- Focus: All constraint relationships
- Parameterization: Constraint types vary, entities vary
- Training: "Apply [constraint] between [entities]" → C# code

### Phase 3: GD&T (Geometric Dimensioning & Tolerancing)
- Source: ASME Y14.5-2018 standard
- Focus: All 14 geometric characteristics
- Parameterization: Tolerance values, datums, modifiers vary
- Training: "Apply [characteristic] [tolerance] relative to [datum]" → C# code

### Phase 4: Design Patterns
- Source: Real-world SolidWorks designs
- Focus: Common part families (holes, pockets, ribs, etc.)
- Parameterization: Each pattern is explored across design space
- Training: Parameter variations → code variations

## Key Innovations

### 1. Parameterization-First Training
Instead of discrete examples, explore parameter spaces.
- 1 parameter space = 1000s of training examples
- Model learns design variability
- Better generalization

### 2. GD&T as First-Class
GD&T is not an afterthought but core to sketch definition.
- Sketches are "fully defined" with GD&T
- Model understands manufacturing intent
- Supports tolerance analysis

### 3. Local LLM Inference
All inference runs locally via Ollama.
- No cloud dependency
- Privacy-preserving
- Deterministic (same hardware, same results)

### 4. MCP Bridge (Optional)
Claude AI integration via Model Context Protocol.
- Claude can query live SolidWorks models
- Claude can generate code in context
- Bidirectional: Claude suggests → Add-in implements

## Design Decisions

### Why Parameter Spaces?
- **Problem**: SolidWorks has infinite design possibilities
- **Solution**: Define finite parameter spaces (sketch, hole, boss, etc.)
- **Benefit**: Training data is generated, not collected
- **Scaling**: Add new parameter spaces = add new training domains

### Why Parameterization in Resolver?
- **Problem**: C# code has many variations for same intent
- **Solution**: Template-based code generation with parameter substitution
- **Benefit**: Code is consistent, readable, maintainable
- **Scaling**: One template serves 1000 use cases

### Why Ollama?
- **Problem**: Cloud LLMs have latency, cost, privacy concerns
- **Solution**: Run fine-tuned model locally in Ollama
- **Benefit**: Instant inference, no external calls, full control
- **Trade-off**: Requires local GPU or CPU

### Why Axolotl + LoRA?
- **Problem**: Full fine-tuning of 7B model is expensive
- **Solution**: LoRA fine-tuning (low-rank adaptation)
- **Benefit**: 50x cheaper, 10x faster, same quality
- **Model**: Qwen2.5-Coder-7B (code understanding)

## Data Flow Example: Parameter → Code → Training

```python
# 1. Define Parameter Space
HOLE_SPACE = ParameterSpace(
    name="mounting_hole",
    parameters={
        "diameter": [5-50mm],
        "x_position": [0-100mm],
        "y_position": [0-100mm],
        "tolerance": [0.05-0.5mm],
        "modifier": ["RFS", "MMC", "LMC"],
    }
)

# 2. Generate Variations
generator = ParameterizationDataGenerator()
pairs = generator.generate_variations(HOLE_SPACE, samples_per_parameter=3)
# Result: 3^5 = 243 training pairs from ONE parameter space!

# 3. Each Pair
(
    "Create a circular hole with diameter 10mm at (25, 15) with 0.1mm tolerance MMC",
    """
    ISketch sketch = part.CreateSketch();
    // ... auto-generated C# code
    IToleranceFeature2 tol = part.CreateToleranceFeature();
    tol.Tolerance1 = 0.1;
    tol.MaterialModifier1 = (int)swMaterialModifier.MMC;
    """
)

# 4. Export to Alpaca Format
generator.export_to_alpaca(pairs, "training_data.json")

# 5. Fine-tune with Axolotl
# $ axolotl train axolotl_config.yml

# 6. Convert to GGUF
# $ ollama create sw-semantic-7b --modelfile Modelfile

# 7. Serve with Ollama
# $ ollama serve
# $ curl http://localhost:11434/api/generate
```

## Extensibility

### Adding a New Parameter Space
```python
# 1. Define it
POCKET_SPACE = ParameterSpace(...)

# 2. Add to training
generator.generate_variations(POCKET_SPACE)

# 3. Export
generator.export_to_alpaca(pairs, "pocket_training.json")

# 4. Combine with existing data
# Merge all JSON files

# 5. Re-train model
# (Takes 2-4 hours on consumer GPU)
```

### Adding a New GD&T Characteristic
```python
# 1. Define in parameter_space.py
PROFILE_SPACE = ParameterSpace(
    parameters={
        "profile_tolerance": ParameterDefinition(...),
        "profile_datum_references": ParameterDefinition(...),
    }
)

# 2. Add resolver templates
resolver.templates["gdt_profile"] = "..."

# 3. Generate training data
pairs = generator.generate_variations(PROFILE_SPACE)
```

## Success Metrics

- **Model Quality**: Can generate valid C# code for unseen SolidWorks tasks
- **Parameterization Coverage**: All parameter domains (sketch, GD&T, feature) represented
- **Training Data**: 5000+ pairs covering 50+ design patterns
- **User Satisfaction**: Add-in consistently generates usable code
- **Inference Speed**: <500ms for code generation (local Ollama)
