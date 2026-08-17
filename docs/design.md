# Seismic interface design

## Product character

Seismic is an engineering instrument for seeing a change propagate through code before
the edit happens. Its visual materials are graphite, survey paper, hazard paint and
oscilloscope traces. The interface is precise and quiet until a blast-radius path is
active, then one orange pulse travels through the evidence graph.

## Tokens

- Background: `#12100e`, warm graphite.
- Raised surface: `#1b1815`.
- Quiet surface: `#24201c`.
- Primary text: `#f5efe6`.
- Muted text: `#aaa097`.
- Border: `#39322c`.
- Accent: `#ff5a24`, hazard orange.
- Critical: `#e83f2d`.
- Warning: `#f3ad32`.
- Verified: `#8fa37b`, muted instrument green used only for health.
- Display: Space Grotesk, 600 to 700.
- Body: Inter, 400 to 600.
- Data: IBM Plex Mono, 400 to 600 with tabular numerals.
- Radius: 8px controls, 10px surfaces and no decorative capsules.
- Motion: 180ms ease-out for state changes, 420ms graph reveals and one 3.2s
  path pulse. All motion stops under `prefers-reduced-motion`.

## Primary dashboard

The desktop app is one bounded command surface, not a grid of unrelated cards.

1. A 64px header carries the fault-line mark, Seismic wordmark, Track 02B label,
   current snapshot and HydraDB connection state.
2. A 252px repository rail owns repository selection, indexing and snapshot evidence.
3. The main canvas renders the selected target and every affected artifact as a real
   inline SVG dependency graph. Edges are labeled with CALLS, IMPORTS, TESTS or
   STARTS_AT. The selected evidence path brightens and pulses from changed code to
   affected code.
4. A 344px impact rail lists ranked artifacts. Selection updates the exact path below
   the graph, including hop lines and incident evidence.
5. A bottom analysis bar owns target entry, hop bound and the primary Analyze change
   action. No other control competes with it.

On tablet the repository rail becomes a top strip and the impact rail moves below the
canvas. On mobile, analysis comes first, followed by a horizontally scrollable graph
inside its own viewport and then the ranked list. The page itself never scrolls
horizontally.

## States

- Empty: explain that a repository must be indexed, then focus the repository path.
- Loading: keep the existing graph visible at reduced contrast and draw a scan line.
- Success: animate one orange path and announce the result count in an ARIA live region.
- Error: show the exact failed operation and a concrete next action near the control.
- No evidence: say that the current snapshot has no supported path within the hop bound.
- Keyboard focus: 2px orange outline with 3px offset.

## Landing page

The landing page uses the same graphite and survey-line system. Its hero is a large
code dependency fault map, not a generic dashboard screenshot. Copy stays specific:
“Know what a code change can break before the agent edits it.” The primary action opens
the analyzer. Sections explain the graph invariant, the four-step agent workflow and
why HydraDB native paths are central. No fake customer logos, pricing or fabricated
performance claims.
