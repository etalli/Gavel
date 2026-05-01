# Gavel Dev Log

---

## 2026-05-01

### Codex Review — working tree diff

**Target:** working tree (modified KiCad PCB files + untracked devlog/gerbers)

**Finding — P1:**

> `hardware/PCB/Gavel-TopPlate.kicad_pcb` lines 61–62
>
> The KiCad board's saved plot configuration now targets only `Edge.Cuts` and a non-Gerber output format (`outputformat` changed from `1` → `5`). Regenerating fabrication outputs from the committed design will produce only an SVG of the board outline, losing the full copper/mask/silkscreen Gerber set. This is a workflow-breaking regression for the hardware release process.

**Action:** Opened [issue #36](https://github.com/etalli/Gavel/issues/36) — later confirmed false alarm and closed. Edge.Cuts SVG output is intentional: it is the laser-cut design file for the top plate acrylic. Plot config is correct.

---

## 2026-04-29

- **feat:** added `stats.py` CLI — reads `~/.claude/gavel/decisions.jsonl` and prints per-button counts, reject rate, and first/last timestamps
- **docs:** updated README to mention `stats.py` and decision log
