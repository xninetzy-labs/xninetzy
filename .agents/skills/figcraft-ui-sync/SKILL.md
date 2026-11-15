---
name: figcraft-ui-sync
description: Keeps UI implementation in sync with the owner's FigCraft design through the `figcraft` MCP; reads colors, type, spacing and components before coding, then updates the FigCraft file to match the shipped UI. Use for any UI implementation, restyle or new screen.
metadata:
  keywords: ui ux frontend tampilan halaman page screen komponen component restyle redesign implement implementasi figcraft figma design desain mockup wireframe prototype style token tailwind css theme layout landing dashboard react vue svelte
---

# FigCraft UI sync

The owner's FigCraft file is the design source for UI work. Code follows its styles, and the file is updated to match what ships. FigCraft is the owner's design tool; the `figma` MCP only reads Figma links the owner provides.

## Workflow

1. **Find the design.** `inspect_ui` lists the app windows and open files when the MCP is attached. If several files or none are open, ask the owner which `.figcraft` file, page and frame belong to this UI, then `open_file`. If the MCP reports a headless session, say that the FigCraft app is not attached (`~/.local/bin/figcraft-mcp` starts it when a display is available).
2. **Read the design system.** `inspect_document`, then `get_node` on the target frames: fills, strokes, font family, size, weight and line height, auto-layout gap and padding, corner radius, effects, components and instances. `list_commands` with the filter `variable` or `style` finds token commands. `screenshot` the frames and look at them.
3. **Map it into code.** Put the values into the project's existing token layer (CSS variables, Tailwind theme, theme file) before writing components. Reuse existing components. Do not introduce colors, fonts or spacing that are absent from the design; when a state is missing (hover, focus, error, empty, loading, mobile), design it from the same tokens and record it for step 5.
4. **Implement** the UI with the project's own conventions and tests.
5. **Update FigCraft to match.** Before the first write in a session, copy the `.figcraft` file on disk to `<name>.bak-<YYYYMMDD-HHMM>.figcraft`. Mirror the shipped UI: change existing frames and components in place, add new screens or states as frames named like their code components, and keep each screen's edit in one `batch` so it is one undo step. Then `save_file`.
6. **Verify both sides.** `screenshot` the updated frames. Compare them with the running UI; ask before browser automation (Playwright) to capture it. Report what matches and every difference you saw.

## Rules

- Work in FigCraft coordinates as the server describes: page units, y down, x/y relative to the parent frame; children of auto-layout frames are placed by the layout properties.
- Open FigCraft comments on the frames are design feedback: read them with the `comment.list` command, fix what applies, reply with what changed.
- A Figma link from the owner: read it with `get_figma_data` (`figma` MCP). FigCraft opens `.fig` files and Figma REST JSON with `open_file`, with warnings for what did not import.
- Component code links: `figcraft-cli connect publish` writes the mappings in a `figcraft.connect.json` into the design file when the owner wants them.
- No design exists yet: agree the direction with the owner (skill `frontend-design` helps), implement, then create the frames in FigCraft in step 5 so the file becomes the source from then on.
- Never claim the design and the UI match without the screenshots from step 6.
