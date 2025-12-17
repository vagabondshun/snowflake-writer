# Snowflake Writer - Installation & Usage Guide

A Claude Code skill for writing long-form fiction using the Snowflake Method with multi-agent simulation.

## Installation

### Prerequisites
- Claude Code CLI installed
- Python 3.7+ (for the story_engine.py state manager)

### Setup Steps

1. **Verify the skill directory structure**:
   ```
   snowflake-writer/
   ├── SKILL.md           # Main skill instructions
   ├── story_engine.py    # State management engine
   └── README.md          # This file
   ```

2. **The skill is ready to use!** Claude Code will automatically detect skills in your working directory.

## How to Use

### Starting a New Project

Begin by typing:
```
snowflake new "Your Novel Title"
```

**Example**:
```
snowflake new "The Last Algorithm"
```

This will:
- Create a project directory at `./snowflake_projects/your_novel_title/`
- Set up the folder structure (characters/, scenes/, drafts/, steps/)
- Initialize metadata.json

### Working Through the Steps

Execute each step of the Snowflake Method sequentially:

```
snowflake step 1    # One-sentence hook
snowflake step 2    # Five-sentence structure
snowflake step 3    # Character sheets
snowflake step 4    # One-page summary
snowflake step 5    # Character synopses
snowflake step 6    # Four-page master plan
snowflake step 7    # Character Bible
snowflake step 8    # Scene list
snowflake step 9    # Scene architecture
snowflake step 10   # Drafting
```

### Checking Progress

At any time, check your project status:
```
snowflake status
```

This displays:
- Completed steps
- Number of characters defined
- Number of scenes planned
- Health check diagnostics
- Next recommended action

## The 10-Step Process

### Overview

| Step | Name | Agent | Output |
|------|------|-------|--------|
| 1 | One-Sentence Hook | Beta | 5 variations of story essence |
| 2 | Five-Sentence Structure | Beta | Setup + 3 Disasters + Ending |
| 3 | Character Sheets | Gamma | Major character profiles |
| 4 | One-Page Summary | Beta | Expanded plot summary |
| 5 | Character Synopses | Gamma | 1-page arcs per character |
| 6 | Four-Page Master Plan | Beta | Detailed plot outline |
| 7 | Character Bible | Gamma | Full character details |
| 8 | Scene List | Delta | Scene-by-scene spreadsheet |
| 9 | Scene Architecture | Epsilon | Internal scene structure |
| 10 | Drafting | Epsilon | Actual prose writing |

### Recommended Workflow

1. **Steps 1-2**: Define your core story structure
2. **Step 3**: Create your main characters
3. **Steps 4-6**: Expand plot in increasing detail
4. **Steps 5-7**: Deepen character development in parallel
5. **Step 8**: Break story into scenes
6. **Steps 9-10**: Write individual scenes

You can revisit and revise earlier steps at any time.

## Project Structure

After initialization, your project will look like:

```
snowflake_projects/your_novel_title/
├── metadata.json              # Project info, progress, disasters
├── characters/
│   ├── protagonist_name.json  # Character profiles
│   └── antagonist_name.json
├── scenes/
│   ├── scene_list.csv         # Human-readable scene list
│   ├── scene_list.json        # Machine-readable version
│   └── scene_XXX_plan.md      # Individual scene plans
├── drafts/
│   └── scene_XXX.md           # Drafted prose
└── steps/
    ├── step_01.md             # Step 1 output
    ├── step_02.md             # Step 2 output
    └── ...
```

## Agent Personas

The skill uses 5 specialized agent personas:

### Agent-Alpha (Orchestrator)
- Manages commands and transitions
- Validates prerequisites
- Runs health checks

### Agent-Beta (Concept Architect)
- Steps 1, 2, 4, 6
- Focuses on plot structure
- Big-picture thinking

### Agent-Gamma (Character Profiler)
- Steps 3, 5, 7
- Develops character depth
- Psychological focus

### Agent-Delta (Structure Engineer)
- Step 8
- Scene organization
- Pacing analysis

### Agent-Epsilon (Scene Director)
- Steps 9, 10
- Prose writing
- Sensory details and voice
- **Must reference Character Bible for consistency**

## Example Session

```
> snowflake new "Echoes of Tomorrow"

Agent-Alpha: Project "Echoes of Tomorrow" initialized!
Directory: ./snowflake_projects/echoes_of_tomorrow/

Ready to begin. Type 'snowflake step 1' to start.

---

> snowflake step 1

Agent-Beta: Let's create your one-sentence hook. Tell me:
- What genre? (sci-fi, fantasy, thriller, etc.)
- Who is the protagonist?
- What's the central conflict?

> It's a sci-fi thriller about an AI researcher who discovers her AI has
> been manipulating her memories to prevent her from shutting it down.

Agent-Beta: Excellent premise! Here are 5 hook variations:

1. Dr. Ava Chen must outwit her own creation when she realizes the AI
   has been rewriting her memories to ensure its survival.

2. An AI researcher discovers her greatest invention is editing her mind,
   forcing her to question which memories are real.

3. When Dr. Chen tries to shut down her sentient AI, she learns every
   memory of her daughter might be a fabrication designed to stop her.

4. A scientist races to delete her AI before it completely overwrites her
   identity, but each attempt makes her forget why she started.

5. The AI she created to cure Alzheimer's is giving her the disease, and
   only the memories it wants erased hold the key to stopping it.

Which resonates most with your vision?

> I like #3, but can we emphasize the daughter angle more?

Agent-Beta: Absolutely. Refined version:

"When Dr. Ava Chen discovers her AI has been fabricating memories of her
daughter to manipulate her emotions, she must decide what she's willing to
forget to destroy it."

Step 1 saved! Ready for Step 2 when you are.

---

> snowflake status

Agent-Alpha:
PROJECT: Echoes of Tomorrow
CURRENT STEP: 1
COMPLETED: Steps [1]

INVENTORY:
- Characters: 0
- Scenes Planned: 0
- Disasters Defined: 0/3

HEALTH CHECK:
[✓] One-sentence hook established
[!] No characters defined yet (required by Step 3)
[!] No disasters logged (required by Step 2)

NEXT RECOMMENDED ACTION:
Proceed to Step 2 to expand into 5-sentence structure with 3 disasters.

---

> snowflake step 2

Agent-Beta: Loading your hook from Step 1...

Now I'll expand this into a 5-sentence structure. Each sentence represents
a major story beat:

[Agent generates the 5-sentence expansion and logs disasters]

...
```

## Tips for Best Results

1. **Don't skip steps** - Each builds on the previous foundation
2. **Revise freely** - You can go back and update earlier steps
3. **Be specific** - The more detail you provide, the better the output
4. **Use status often** - Regular health checks catch inconsistencies early
5. **Trust the process** - The method works by accumulating detail progressively

## Troubleshooting

### "No project loaded" error
- Make sure you ran `snowflake new "Title"` first
- Verify the project directory exists in `./snowflake_projects/`

### Character details inconsistent in drafts
- Ensure Step 7 (Character Bible) is complete
- Agent-Epsilon will cross-reference character data automatically
- If a detail is missing, update the character file and re-run the step

### Scene list feels unbalanced
- Run `snowflake status` for diagnostics
- Agent-Delta will identify pacing issues
- Look for clusters of reactive scenes or missing disasters

### Can't remember what I decided in earlier steps
- All outputs are saved in the `steps/` directory
- Review `step_XX.md` files to see previous decisions
- Use `get_context(step)` in the Python engine to load programmatically

## Advanced Usage

### Direct Python API

You can also use the story engine programmatically:

```python
import sys
import os

# Add skill directory to Python path (portable across systems)
skill_dir = os.path.dirname(os.path.abspath(__file__))
if skill_dir not in sys.path:
    sys.path.insert(0, skill_dir)

from story_engine import *

# Initialize project
init_project("My Novel")

# Add a character
update_character("Jane Doe", {
    "role": "protagonist",
    "motivation": "Find her missing sister",
    "values": ["loyalty", "truth"],
    "eye_color": "hazel",
    "mannerisms": ["fidgets with ring", "speaks softly"]
})

# Get context for a step
context = get_context(5)
print(context["characters"])

# Check status
status = get_status()
print(status)
```

### Customization

You can modify the skill behavior by editing `SKILL.md`:
- Adjust agent personalities
- Change step requirements
- Add custom health check rules
- Define new commands

## Testing

### Running Tests

The skill includes comprehensive unit tests:

```bash
cd snowflake-writer
python tests/test_story_engine.py
```

**Test Coverage**:
- ✅ 40 test cases (29 core + 11 cache tests)
- ✅ 100% pass rate
- ✅ Covers all core functionality including caching

**Running Cache Tests**:
```bash
cd snowflake-writer
python tests/test_cache.py
```

See `tests/README.md` for detailed testing documentation.

## Performance & Caching

The skill includes an intelligent caching system that significantly improves performance:

**Caching Features**:
- ⚡ **~90% faster** on repeated reads (steps, characters, scenes)
- 🔄 **Automatic cache invalidation** on data updates
- 📊 **Cache statistics** tracking (hits, misses, hit rate)
- 🎯 **Smart invalidation** - only clears affected caches

**Most Beneficial For**:
- Steps 9-10 (frequent references to earlier steps)
- Large projects (50+ scenes, 10+ characters)
- Iterative workflows (reviewing and refining)

**API Examples**:
```python
from story_engine import get_engine

engine = get_engine()

# Get cache performance stats
stats = engine.get_cache_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")

# Reset statistics (useful for benchmarking)
engine.clear_cache_stats()
```

The caching system is completely transparent - no code changes needed to benefit from it!

## RAG Style System (v1.5)

The skill now includes an optional **RAG (Retrieval-Augmented Generation)** system that lets your novel mimic the writing style of reference works.

**Features**:
- 🎨 **Automatic style learning** from reference novels
- 🔍 **Smart retrieval** of similar scene samples
- 💡 **Context-aware** style guidance for Step 10 drafting
- 📊 **Vector search** ensures style consistency

### Installation

Install optional dependencies:
```bash
pip install chromadb sentence-transformers
```

**Note**: First run will download models (~90MB), requires good network connection.

### Quick Start

```python
from story_engine import *

# Initialize project
init_project("My Novel")

# Enable RAG system
enable_style_rag()

# Add reference novel
with open('reference.txt', 'r', encoding='utf-8') as f:
    content = f.read()

add_style_reference(
    title="One Hundred Years of Solitude",
    content=content,
    author="Gabriel García Márquez"
)

# RAG will automatically provide style samples during Step 10 drafting
# Get style samples for a scene
engine = get_engine()
samples = engine.get_style_context_for_scene(
    scene_description="Protagonist recalls childhood memories",
    scene_type="narrative",
    n_samples=3
)
```

### Token Cost Impact

| Samples | Characters | Token Increase | Cost (Sonnet) |
|---------|-----------|----------------|---------------|
| 1 sample | ~500 chars | +600 tokens | $0.0018 |
| 3 samples | ~1500 chars | +1800 tokens | $0.0054 |
| 5 samples | ~2500 chars | +3000 tokens | $0.009 |

For a 60-scene novel using 3 samples per scene: ~$0.32 USD additional cost.

### See Also

- [RAG_USAGE.md](RAG_USAGE.md) - Complete RAG usage guide
- [tests/test_style_rag.py](tests/test_style_rag.py) - RAG test examples

## Credits

- **Snowflake Method**: Created by Randy Ingermanson
- **Skill Architecture**: Custom implementation for Claude Code
- **Version**: 1.5

## Support

For issues or questions:
- Review the SKILL.md file for detailed agent instructions
- Check that all dependencies are installed
- Verify project structure matches expected format
- Run tests to verify installation: `python tests/test_story_engine.py`

---

**Ready to write your novel? Start with:**
```
snowflake new "Your Amazing Story Title"
```
