# Walkthrough - Custom Character Integration

I have successfully integrated the custom character "Rin" into the video pipeline frontend and Remotion project.

## Changes

### Frontend
- **Updated `index.html`**: Added "Rin (オリジナル)" to the character selection dropdown.

### Backend (Server)
- **Updated `server.py`**:
    - Added logic to handle `custom-rin` selection.
    - Sets character visibility to `True`.
    - Automatically copies `rin.png` and mouth assets (A-F) from `video-pipeline/character` to `remotion-project/public/character` when selected.
    - **FIX**: Removed `characterBase` setting for Rin to prevent double rendering (stand effect), as mouth images are full-body.
    - Configures the pipeline to use these specific assets.
    - Sets default voice to "春日部つむぎ" (ID: 8) for Rin.

### Pipeline Logic
- **Updated `scripts/integrate_data.py`**:
    - Now accepts `characterBase` and `characterMouthDir` from the input script.
    - Passes these values to the final `pipeline-data.json`.

### Remotion Project
- **Updated `src/types/pipeline.ts`**: Added `characterBase` and `characterMouthDir` to the `VideoConfig` interface.
- **Updated `src/MultiSceneVideo.tsx`**: Extracts these new config values and passes them to the `<Character />` component, enabling dynamic character switching.

## Verification Results

### Automated Verification
- **Pipeline Data Logic**: I manually ran `integrate_data.py` with a test script containing the new character configuration.
- **Result**: The generated `pipeline-data.json` correctly included:
  ```json
  "videoConfig": {
    "characterBase": "character/rin.png",
    "characterMouthDir": "character",
    ...
  }
  ```
  This confirms the data flow from the script to the Remotion pipeline is correct.

## How to Test

1.  **Restart the Server**:
    > [!IMPORTANT]
    > You must **stop** (Ctrl+C) and **restart** the running `python server.py` command in your terminal for the changes to take effect.

2.  **Generate a Video**:
    - Open `http://localhost:8000`.
    - Select "Rin (オリジナル)" in the characters dropdown.
    - Create a video as usual.
    - The generated video should feature the Rin character with lip-syncing.
