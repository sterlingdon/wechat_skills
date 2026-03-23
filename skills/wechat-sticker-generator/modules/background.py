import os
import sys
import tempfile
import subprocess
import numpy as np
from PIL import Image

REMBG_SESSIONS = {}

def _sharpen_alpha_edges(img, threshold=200):
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    try:
        arr = np.array(img)
        alpha = arr[:,:,3]

        mask = (alpha > 50) & (alpha < threshold)

        if not np.any(mask):
            return img

        arr[mask, 3] = np.where(alpha[mask] > threshold // 2, 255, 0)

        return Image.fromarray(arr)
    except ImportError:
        return img

def _remove_background_with_rembg(img, model_name="isnet-anime", alpha_matting=True):
    try:
        from rembg import remove, new_session
    except ImportError:
        raise RuntimeError("rembg 未安装，请先执行: pip install rembg")

    session = REMBG_SESSIONS.get(model_name)
    if session is None:
        session = new_session(model_name)
        REMBG_SESSIONS[model_name] = session

    if img.mode != "RGBA":
        img = img.convert("RGBA")

    out_img = remove(img, session=session, alpha_matting=alpha_matting)

    if out_img.mode != "RGBA":
        out_img = out_img.convert("RGBA")
    return out_img

def _remove_background_via_local_script(img, script_path, model_name="isnet-general-use"):
    if not script_path:
        raise RuntimeError("未提供 bg_removal_script_path")

    abs_script = os.path.abspath(script_path)
    if not os.path.isfile(abs_script):
        raise RuntimeError(f"本地脚本不存在: {abs_script}")

    with tempfile.TemporaryDirectory() as td:
        in_path = os.path.join(td, "input.png")
        out_path = os.path.join(td, "output.png")
        img.save(in_path, "PNG")

        attempts = [
            [sys.executable, abs_script, "--input", in_path, "--output", out_path, "--model", model_name],
            [sys.executable, abs_script, in_path, out_path],
        ]

        last_error = None
        for cmd in attempts:
            try:
                result = subprocess.run(cmd, check=False, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(out_path):
                    out_img = Image.open(out_path)
                    if out_img.mode != "RGBA":
                        out_img = out_img.convert("RGBA")
                    return out_img
                last_error = result.stderr.strip() or result.stdout.strip() or f"exit={result.returncode}"
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(f"调用本地抠图脚本失败: {last_error}")

def apply_background_removal(img, bg_cfg):
    if not bg_cfg.get("enabled"):
        return img

    method = str(bg_cfg.get("method", "rembg")).strip().lower()
    model_name = bg_cfg.get("model", "isnet-anime")
    script_path = bg_cfg.get("script_path", "")
    alpha_matting = bg_cfg.get("alpha_matting", True)
    sharpen_edges = bg_cfg.get("sharpen_edges", False)
    sharpen_threshold = bg_cfg.get("sharpen_threshold", 200)

    try:
        if method == "script":
            out = _remove_background_via_local_script(img, script_path=script_path, model_name=model_name)
        elif method == "opencv":
            from modules.bg_opencv import remove_background_opencv
            out = remove_background_opencv(img)
        elif method == "rembg":
            out = _remove_background_with_rembg(img, model_name=model_name, alpha_matting=alpha_matting)
        else:
            print(f"[!] Unknown bg_removal_method={method}, using rembg", file=sys.stderr)
            out = _remove_background_with_rembg(img, model_name=model_name, alpha_matting=alpha_matting)

        # Sanitize alpha: zero out very faint residues (prevents ghosting/flicker in GIFs)
        if out is not None and out.mode == "RGBA":
            arr = np.array(out)
            arr[arr[:,:,3] < 10, 3] = 0
            out = Image.fromarray(arr)

        if sharpen_edges:
            out = _sharpen_alpha_edges(out, threshold=sharpen_threshold)

        return out
    except Exception as e:
        print(f"[!] Background removal failed ({method}): {e}", file=sys.stderr)
        print("[*] Keeping original image for this frame.", file=sys.stderr)
        return img
