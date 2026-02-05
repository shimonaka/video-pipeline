# Implementation Plan - Custom Character Integration

The goal is to make the custom "Rin" character (PNGTuber style) usable from the Frontend UI.
Currently, the character assets exist in `video-pipeline/character` but are not fully integrated into the Frontend -> Server -> Remotion pipeline.

## User Review Required

> [!IMPORTANT]
> This change introduces a new "Custom Character" option in the Frontend. 
> The character assets (Rin) will be used when this option is selected.
> Assets will be copied from `character/` to `remotion-project/public/character/` dynamically or on-demand.

## Proposed Changes

### Frontend
#### [MODIFY] [index.html](file:///c:/Users/shimo/Desktop/miyabi/Miyabi/video-pipeline/frontend/static/index.html)
- Add "Rin (Custom)" option to the `#speaker` select dropdown.

### Backend (Server)
#### [MODIFY] [server.py](file:///c:/Users/shimo/Desktop/miyabi/Miyabi/video-pipeline/frontend/server.py)
- Update `generate_video` endpoint to handle the new `custom-rin` speaker value.
- When `custom-rin` is selected:
    - Set `characterVisible` to `True`.
    - Set `characterBase` to `character/rin.png`.
    - Set `characterMouthDir` to `character`.
    - Copy `video-pipeline/character/rin.png` to `remotion-project/public/character/rin.png`.
    - Ensure mouth images are present (likely already there, but verified).

### Pipeline Scripts
#### [MODIFY] [integrate_data.py](file:///c:/Users/shimo/Desktop/miyabi/Miyabi/video-pipeline/scripts/integrate_data.py)
- Update `integrate_pipeline_data` to read `characterBase` and `characterMouthDir` from the input script's `video` section.
- Include these fields in the generated `pipeline-data.json` under `videoConfig`.

### Remotion Project
#### [MODIFY] [pipeline.ts](file:///c:/Users/shimo/Desktop/miyabi/Miyabi/video-pipeline/remotion-project/src/types/pipeline.ts)
- Update `VideoConfig` interface to include optional `characterBase` (string) and `characterMouthDir` (string).

#### [MODIFY] [MultiSceneVideo.tsx](file:///c:/Users/shimo/Desktop/miyabi/Miyabi/video-pipeline/remotion-project/src/MultiSceneVideo.tsx)
- extract `characterBase` and `characterMouthDir` from `videoConfig`.
- Pass these values to the `<Character />` component.

## Verification Plan

### Automated Tests
- None existing for the full UI flow.

### Manual Verification
1.  **Start Server**: Run `python frontend/server.py`.
2.  **Access UI**: Open `http://localhost:8000` (I can use `curl` to simulate the POST request).
3.  **Generate Video**:
    - Select "Rin (Custom)" as character.
    - Submit a request.
4.  **Check Output**:
    - Verify `pipeline-data.json` in `remotion-project/public` contains `characterBase: "character/rin.png"`.
    - Verify `remotion-project/public/character/rin.png` exists.
    - (Optional) Run `npx remotion render` manually if the pipeline doesn't finish, or check the server logs for success.
