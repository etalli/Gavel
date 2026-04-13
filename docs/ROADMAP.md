# Gavel Roadmap

## Phase 1 — Polish

Quick wins requiring no new hardware. Focus on correctness and clean behavior.

| Issue | Title |
|-------|-------|
| [#3](https://github.com/etalli/Gavel/issues/3) | Stop hook: turn off LEDs when Claude Code session ends |
| [#6](https://github.com/etalli/Gavel/issues/6) | Remove misleading `BAUD_RATE` constant in `pico.py` |
| [#8](https://github.com/etalli/Gavel/issues/8) | Remove unused `press_enter()` from firmware |

## Phase 2 — Smarter Feedback

Richer visual feedback and decision logging. No new hardware required.

| Issue | Title |
|-------|-------|
| [#9](https://github.com/etalli/Gavel/issues/9) | Show last decision on LED after button press |
| [#4](https://github.com/etalli/Gavel/issues/4) | LED patterns per tool category in PreToolUse |
| [#5](https://github.com/etalli/Gavel/issues/5) | Reverse serial: log button decisions from Pico to Mac |

## Phase 3 — Hardware Expansion

New components and board support. Requires hardware changes.

| Issue | Title |
|-------|-------|
| — | Physical feedback: buzzer or haptic motor on GP13 (see `implementation_plan.md`) |
| [#10](https://github.com/etalli/Gavel/issues/10) | Solenoid support to animate Claude character on events |
| [#2](https://github.com/etalli/Gavel/issues/2) | Support alternative hardware (Seeed XIAO RP2040) |

---

## Out of Scope

| Issue | Title | Notes |
|-------|-------|-------|
| [#1](https://github.com/etalli/Gavel/issues/1) | Add Japanese documentation | Separate from feature development |
