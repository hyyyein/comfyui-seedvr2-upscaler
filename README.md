# ComfyUI SeedVR2 Batch Upscaler

Batch upscales images in the script folder by enqueueing a SeedVR2 workflow through the ComfyUI API.

## Requirements

- Python 3
- ComfyUI running locally
- SeedVR2 video upscaler custom nodes installed in ComfyUI
- These model files available to the SeedVR2 nodes:
  - `ema_vae_fp16.safetensors`
  - `seedvr2_ema_7b_sharp_fp16.safetensors`

## Usage

Put source images next to `upscale.py`, then run:

```powershell
python .\upscale.py --name output_prefix --input-dir "C:\path\to\ComfyUI\input"
```

Optional environment variables:

```powershell
$env:COMFYUI_URL = "http://localhost:8002"
$env:COMFYUI_INPUT_DIR = "C:\path\to\ComfyUI\input"
python .\upscale.py --name output_prefix
```

On Windows, you can also run `upscale.bat` and enter the values when prompted.

Completed source images are moved into `done/`. Generated upscaled files are saved by ComfyUI according to the `SaveImage` node output settings.

## Notes

- Files with `_upscale` in the name are skipped.
- Supported input extensions are `.png`, `.jpg`, `.jpeg`, and `.webp`.
- Local machine paths, outputs, and image files are intentionally excluded from version control.
