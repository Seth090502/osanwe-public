---
categories:
  - entity
created: <% tp.date.now("YYYY-MM-DD") %>
updated: <% tp.date.now("YYYY-MM-DD") %>
status: active
tags: []
aliases: []
related: []
---

# <% tp.file.title %>

## Overview

## Analyses
```base
filters:
  - file.inFolder("wiki/investing/analyses")
  - file.tags.contains("ticker/<% tp.file.title %>")
  - type == "analysis"
views:
  - type: table
    name: analyses
    order: [file.name, confidence, updated]
    sort:
      - column: updated
        direction: DESC
```

## Key Catalysts

## Notes
> Quick observations, linked from daily notes

Related: 
