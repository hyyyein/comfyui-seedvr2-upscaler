import argparse
import copy
import json
import mimetypes
import os
import shutil
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


DEFAULT_COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")
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


def encode_multipart_formdata(fields, files):
    boundary = f"----ComfyUIUpscaler{uuid.uuid4().hex}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
        )
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for name, filename, content, mime_type in files:
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8")
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"))
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def upload_image(comfyui_url, image_path, upload_filename):
    mime_type = mimetypes.guess_type(upload_filename)[0] or "application/octet-stream"
    body, content_type = encode_multipart_formdata(
        fields={"overwrite": "true", "type": "input"},
        files=[("image", upload_filename, image_path.read_bytes(), mime_type)],
    )
    req = urllib.request.Request(
        f"{comfyui_url.rstrip('/')}/upload/image",
        data=body,
        headers={
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        },
    )

    with urllib.request.urlopen(req) as resp:
        payload = resp.read().decode("utf-8")
        result = json.loads(payload) if payload else {}

    filename = result.get("name", upload_filename)
    subfolder = result.get("subfolder")
    if subfolder:
        return f"{subfolder}/{filename}"
    return filename


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

    images = get_images(folder)
    if not images:
        print("No images found.")
        return

    done_dir = folder / "done"
    done_dir.mkdir(exist_ok=True)

    print(f"Found {len(images)} images. Starting upscale...\n")

    for index, image_path in enumerate(images, 1):
        output_name = f"{args.name}_{index}"
        upload_filename = f"{output_name}{image_path.suffix.lower()}"

        print(f"[{index}/{len(images)}] {image_path.name} -> {output_name}")
        uploaded_filename = upload_image(args.comfyui_url, image_path, upload_filename)
        print(f"  Uploaded: {uploaded_filename}")

        prompt_id = enqueue(args.comfyui_url, uploaded_filename, output_name)
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
