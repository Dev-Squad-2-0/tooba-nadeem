"""
Entity and input resolution utilities for the AFL LangGraph system.

This module is reserved for resolving natural-language AFL references
into the exact entities expected by the prediction and retrieval tools.

Examples of intended resolution include:

```
"Pies"      -> "Collingwood"
"Magpies"   -> "Collingwood"
"Cats"      -> "Geelong"
"this week" -> the relevant fixture date
```

The current graph passes prediction and retrieval inputs through the
corresponding nodes, while the prediction tools perform the required
input validation and model execution.

This module is kept as the dedicated location for future entity/date
resolution logic so that routing, resolution, prediction, and response
formatting remain separate responsibilities.
"""
