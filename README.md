# ComfyUI SeedVR2 일괄 업스케일러

ComfyUI API에 SeedVR2 업스케일 워크플로우를 넣어서, 폴더 안의 이미지를 순서대로 업스케일하는 배치 스크립트입니다.

개인 PC 경로, 결과 이미지, 임시 파일은 저장소에 포함하지 않았습니다. 이미지는 ComfyUI API로 업로드하므로 사용자가 자기 ComfyUI `input` 폴더 경로를 알 필요가 없습니다.

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
python .\upscale.py --name character
```

ComfyUI를 기본 포트가 아닌 다른 포트로 실행 중이면 주소를 지정합니다.

```powershell
python .\upscale.py --name character --comfyui-url "http://localhost:<포트번호>"
```

매번 같은 주소를 쓰는 경우 환경 변수로 지정할 수 있습니다.

```powershell
$env:COMFYUI_URL = "http://localhost:<포트번호>"
python .\upscale.py --name character
```

Windows에서는 `upscale.bat`을 실행한 뒤 안내에 따라 값을 입력해도 됩니다.

## 기본값

- 기본 ComfyUI 주소는 `http://localhost:8188`입니다.
- 출력 파일명은 `--name` 값에 번호를 붙여 만듭니다. 예: `character_1`, `character_2`
- 이미지 하나당 기본 대기 시간은 600초입니다. 필요하면 `--timeout`으로 바꿀 수 있습니다.

## 동작 방식

- 현재 폴더의 `.png`, `.jpg`, `.jpeg`, `.webp` 파일을 찾습니다.
- 파일명에 `_upscale`이 들어간 이미지는 건너뜁니다.
- 이미지를 ComfyUI API의 `/upload/image`로 업로드합니다.
- ComfyUI API에 SeedVR2 워크플로우를 큐로 넣습니다.
- 작업이 완료된 원본 이미지는 `done/` 폴더로 이동합니다.
- 업스케일 결과물은 ComfyUI의 `SaveImage` 노드 설정에 따라 저장됩니다.

## 저장소에 포함하지 않는 것

- 개인 PC의 절대 경로
- 원본 이미지와 업스케일 결과 이미지
- `done/` 폴더
- 캐시와 임시 파일
