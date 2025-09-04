StrOptix Starter Pack
=====================
Files you can edit to drive the tool without touching code.

1) config.yaml
   - Feature flags and simple geometry heuristics (depth ranges, segment rules).
   - Toggle checks on/off (e.g., enable_bending_check).

2) plate_library.xlsx
   - Two sheets: 'web' and 'flange' holding available plate sizes.
   - Replace values with your fabricator's real inventory.

3) code_limits.json
   - Placeholders for IS 800 and AISC 360 limits and coefficients.
   - Populate b/t (flange & web), gamma factors, and shear/LTB notes based on your selected clauses.

4) input_template.xlsx
   - Single-row example of the inputs your UI or CLI expects.
   - Duplicate rows for multiple runs, or pipe via CLI.

5) output_template.xlsx
   - Header-only file showing the exact 'MEMBER TABLE' columns your client expects.

Recommended next steps:
- Replace plate_library.xlsx with real sizes used by your shop.
- Fill code_limits.json with limits/constants from IS 800 or AISC 360 that your engineers use.
- If you want segment lengths to follow bay spacing, set 'segment_rule: by_bay_spacing' in config.yaml.
