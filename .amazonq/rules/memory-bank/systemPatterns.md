# System Patterns

## Architecture
- No application architecture defined yet — project is in initial setup

## Project Structure
```
kiro-dev-workshop/
└── .amazonq/
    └── rules/
        └── memory-bank/    # Persistent context files for Amazon Q
```

## Design Patterns
- Memory Bank pattern: markdown files in `.amazonq/rules/memory-bank/` provide persistent context
- Rules are automatically included in Kiro context for every interaction

## Conventions
- Memory Bank files should be updated as the project evolves
- Keep documentation concise and actionable
