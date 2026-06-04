import argparse
import copy
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8002")
DEFAULT_INPUT_DIR = os.environ.get("COMFYUI_INPUT_DIR")
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

WORKFLOW_TEMPLATE = {
    "10": {
        "inputs": {
            "seed": 42,
            "resolution": 4096,
            "max_resolution": 4096,
            "batch_size": 1,
            "uniform_batch_size": False,
            "color_correction": "lab",
            "temporal_overlap": 0,
            "prepend_frames": 0,
            "input_noise_scale": 0,
            "latent_noise_scale": 0,
            "offload_device": "cpu",
            "enable_debug": False,
            "image": ["17", 0],
            "dit": ["14", 0],
            "vae": ["13", 0],
        },
        "class_type": "SeedVR2VideoUpscaler",
    },
    "13": {
        "inputs": {
            "model": "ema_vae_fp16.safetensors",
            "device": "cuda:0",
            "encode_tiled": True,
            "encode_tile_size": 1024,
            "encode_tile_overlap": 128,
            "decode_tiled": True,
            "decode_tile_size": 1024,
            "decode_tile_overlap": 128,
            "tile_debug": "false",
            "offload_device": "cpu",
            "cache_model": False,
        },
        "class_type": "SeedVR2LoadVAEModel",
    },
    "14": {
        "inputs": {
            "model": "seedvr2_ema_7b_sharp_fp16.safetensors",
            "device": "cuda:0",
            "blocks_to_swap": 36,
            "swap_io_components": False,
            "offload_device": "cpu",
            "cache_model": False,
            "attention_mode": "sdpa",
        },
        "class_type": "SeedVR2LoadDiTModel",
    },
    "15": {
        "inputs": {"filename_prefix": "", "images": ["10", 0]},
        "class_type": "SaveImage",
    },
    "16": {
        "inputs": {"image": ""},
        "class_type": "LoadImage",
    },
    "17": {
        "inputs": {"image": ["16", 0], "alpha": ["16", 1]},
        "class_type": "JoinImageWithAlpha",
    },
}


def api_request(comfyui_url, endpoint, data=None):
    url = f"{comfyui_url.rstrip('/')}{endpoint}"
    if data is not None:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
    else:
        req = urllib.request.Request(url)

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enqueue(comfyui_url, image_filename, output_prefix):
    workflow = copy.deepcopy(WORKFLOW_TEMPLATE)
    workflow["16"]["inputs"]["image"] = image_filename
    workflow["15"]["inputs"]["filename_prefix"] = output_prefix
    result = api_request(comfyui_url, "/prompt", {"prompt": workflow})
    return result["prompt_id"]


def wait_for_completion(comfyui_url, prompt_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = api_request(comfyui_url, f"/history/{prompt_id}")
            if prompt_id in history:
                status = history[prompt_id].get("status", {})
                if status.get("completed", False):
                    return True
                if status.get("status_str") == "error":
                    return False
        except urllib.error.URLError:
            pass
        time.sleep(5)
    return False


def get_images(folder):
    images = []
    for file_path in sorted(folder.iterdir()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() in IMAGE_EXTS and "_upscale" not in file_path.name.lower():
            images.append(file_path)
    return images


def parse_args():
    parser = argparse.ArgumentParser(description="ComfyUI SeedVR2 batch upscaler")
    parser.add_argument("--name", required=True, help="Output filename prefix")
    parser.add_argument(
        "--input-dir",
        default=DEFAULT_INPUT_DIR,
        help="ComfyUI input directory. Can also be set with COMFYUI_INPUT_DIR.",
    )
    parser.add_argument(
        "--comfyui-url",
        default=DEFAULT_COMFYUI_URL,
        help="ComfyUI server URL. Can also be set with COMFYUI_URL.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout per image in seconds (default: 600)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    folder = Path(__file__).resolve().parent
    input_dir = Path(args.input_dir).expanduser().resolve() if args.input_dir else None

    if input_dir is None:
        raise SystemExit(
            "Missing ComfyUI input directory. Pass --input-dir or set COMFYUI_INPUT_DIR."
        )
    if not input_dir.exists():
        raise SystemExit(f"ComfyUI input directory does not exist: {input_dir}")

    images = get_images(folder)
    if not images:
        print("No images found.")
        return

    done_dir = folder / "done"
    done_dir.mkdir(exist_ok=True)

    print(f"Found {len(images)} images. Starting upscale...\n")

    for index, image_path in enumerate(images, 1):
        output_name = f"{args.name}_{index}"
        input_filename = f"{output_name}.png"
        input_path = input_dir / input_filename

        shutil.copy2(image_path, input_path)
        print(f"[{index}/{len(images)}] {image_path.name} -> {output_name}")

        prompt_id = enqueue(args.comfyui_url, input_filename, output_name)
        print(f"  Queued: {prompt_id}")

        print("  Waiting...", end="", flush=True)
        success = wait_for_completion(args.comfyui_url, prompt_id, timeout=args.timeout)

        if success:
            print(" OK")
            shutil.move(str(image_path), done_dir / image_path.name)
            print(f"  -> done/{image_path.name}")
        else:
            print(" FAILED (original kept)")

    print("\nFinished!")


if __name__ == "__main__":
    main()
