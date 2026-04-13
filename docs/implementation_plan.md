# Implement Physical Feedback

This implementation plan outlines the steps to introduce support for a physical feedback mechanism (e.g., a vibration motor or piezo buzzer) that activates alongside the existing LEDs to provide tactile/auditory status updates.

## Proposed Changes

### 1. Hardware Allocation
- **Wire the feedback device** to an unused GPIO pin. We will use **GP13** (Pin 17), which is directly adjacent to the existing LED pins (`GP10`, `GP11`, `GP12`).

### 2. Firmware (`firmware/code.py`)
- Initialize `board.GP13` as a digital output.
- Add helper functions (`pulse_feedback(duration)`, etc.) to provide distinct feedback patterns.
- Hook the feedback into the existing serial command events:
  - `PreToolUse`: 1 short pulse (e.g., 100ms) to indicate Claude Code is waiting for input.
  - `Notification (warn)`: 3 short pulses.
  - `Notification (error)`: 1 steady long pulse (e.g., 500ms).

### 3. Documentation Updates
#### [MODIFY] `hardware/wiring.md`
- Add a new section detailing how to wire the physical feedback component to GP13 (e.g., calling out the need for a transistor/MOSFET if using a high-current motor).

#### [MODIFY] `docs/index.html` & `README.md`
- Safely re-introduce the changes previously reverted, updating the feature tables and text to highlight the new "haptic/physical feedback" capabilities.

## Open Questions

> [!IMPORTANT]
> 1. **Pin preference**: Are you okay with using `GP13`?
> 2. **Component Type**: What type of physical component are you using (Piezo buzzer, logic-level haptic motor, etc.)? This helps clarify if we just need a simple HIGH/LOW digital out or if we should configure a PWM output.
> 3. **Feedback Patterns**: Do the proposed duration patterns (1 pulse for wait, 3 for warn, 1 long for error) fit your use case?

## Verification Plan
- Flash the updated `firmware/code.py` manually via the REPL / serial port or verify its syntax locally.
- Test the output table and hooks using the provided `hooks/test_hooks.py`.
