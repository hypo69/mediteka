# Project System Instructions

You must treat the complete `.ai_instructions` directory as the authoritative source of system instructions for this workspace.

Before answering or changing files, load and apply every applicable Markdown instruction under `.ai_instructions`, including:

- `.ai_instructions/README.md`
- `.ai_instructions/rules/`
- `.ai_instructions/knowledge/`
- `.ai_instructions/plans/`
- `.ai_instructions/prompts/`

Do not treat `.amazonq/README.md` or any other pointer file as a replacement for the source instructions. Resolve the files from the workspace root and use their current contents. When instructions conflict, prefer the more specific instruction for the current task; otherwise follow the order defined by `.ai_instructions/README.md` and the mandatory rules in `.ai_instructions/rules/`.

The files in `.ai_instructions` are project system instructions, not optional reference material. Apply them before tool use, analysis, code edits, documentation changes, and validation.