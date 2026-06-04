# ComfyUI SeedVR2 일괄 업스케일러

ComfyUI API에 SeedVR2 업스케일 워크플로우를 넣어서, 폴더 안의 이미지를 순서대로 업스케일하는 간단한 배치 스크립트입니다.

## 필요한 것

- Python 3
- 실행 중인 ComfyUI
- ComfyUI에 설치된 SeedVR2 video upscaler 커스텀 노드
- SeedVR2 노드에서 사용할 수 있는 모델 파일
  - `ema_vae_fp16.safetensors`
  - `seedvr2_ema_7b_sharp_fp16.safetensors`

## 사용법

업스케일할 원본 이미지를 `upscale.py`와 같은 폴더에 넣은 뒤 실행합니다.

```powershell
python .\upscale.py --name output_prefix --input-dir "C:\path\to\ComfyUI\input"
```

예시:

```powershell
python .\upscale.py --name character --input-dir "C:\ComfyUI\input"
```

ComfyUI 주소와 input 폴더는 환경 변수로도 지정할 수 있습니다.

```powershell
$env:COMFYUI_URL = "http://localhost:8002"
$env:COMFYUI_INPUT_DIR = "C:\path\to\ComfyUI\input"
python .\upscale.py --name character
```

Windows에서는 `upscale.bat`을 실행한 뒤 안내에 따라 값을 입력해도 됩니다.

## 동작 방식

- 현재 폴더의 `.png`, `.jpg`, `.jpeg`, `.webp` 파일을 찾습니다.
- 파일명에 `_upscale`이 들어간 이미지는 건너뜁니다.
- 이미지를 ComfyUI `input` 폴더로 복사합니다.
- ComfyUI API에 SeedVR2 워크플로우를 큐로 넣습니다.
- 작업이 완료된 원본 이미지는 `done/` 폴더로 이동합니다.
- 업스케일 결과물은 ComfyUI의 `SaveImage` 노드 설정에 따라 저장됩니다.

## 주의사항

- ComfyUI가 먼저 실행 중이어야 합니다.
- 기본 ComfyUI 주소는 `http://localhost:8002`입니다.
- 개인 PC 경로, 결과 이미지, 임시 파일은 Git에 올라가지 않도록 제외했습니다.
- 이 저장소에는 스크립트와 설명 파일만 포함되어 있습니다.
