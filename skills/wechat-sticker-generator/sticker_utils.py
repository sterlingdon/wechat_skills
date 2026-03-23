import os
import sys
from datetime import datetime

from modules.config import config_command
from modules.prompts import build_prompts_workspace, build_transform_photo_prompt, build_character_reference_prompt
from modules.api import transform_photo_to_chibi, draw_character_reference, remote_draw_trigger
from modules.postprocess import process_workspace
from modules.meta import generate_meta, process_all_meta

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SKILL_DIR, "output")

def create_dir(provider=None):
    """在 skill 目录下的 output/ 中创建时间戳工作空间"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    if provider:
        timestamp_dir = f"{timestamp_dir}_{provider}"
    full_path = os.path.join(OUTPUT_DIR, timestamp_dir)
    os.makedirs(full_path, exist_ok=True)
    out_dir_abs = os.path.abspath(full_path)
    print(out_dir_abs)
    return out_dir_abs

def _parse_provider_arg(args):
    """从参数列表中解析 --provider 参数"""
    provider = None
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == "--provider" and i + 1 < len(args):
            provider = args[i + 1]
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return provider, remaining

if __name__ == "__main__":
    # 先解析 --provider 参数
    provider_arg, remaining_argv = _parse_provider_arg(sys.argv[1:])

    if not remaining_argv:
        print("Usage:")
        print("  python3 sticker_utils.py create_dir")
        print("  python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description]")
        print("  python3 sticker_utils.py draw_character <character_prompt> <style_preset> <output_path>")
        print("  python3 sticker_utils.py build_prompts <target_directory_path>")
        print("  python3 sticker_utils.py draw <prompt.txt> <output_original_grid.png> [reference_image]")
        print("  python3 sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image>")
        print("  python3 sticker_utils.py process <target_directory_path>")
        print("  python3 sticker_utils.py wechat_meta <target_directory_path|all>")
        print("")
        print("可选参数:")
        print("  --provider <gemini|qwen>  指定 API 提供商（默认从配置或环境变量读取）")
        print("")
        print("环境变量:")
        print("  GEMINI_API_KEY     Gemini API Key")
        print("  DASHSCOPE_API_KEY  千问 API Key")
        print("")
        print("配置管理:")
        print("  python3 sticker_utils.py config                    # 显示当前配置")
        print("  python3 sticker_utils.py config set <provider>     # 设置 API Key")
        print("  python3 sticker_utils.py config default <provider> # 设置默认 provider")
        sys.exit(1)

    cmd = remaining_argv[0]

    if cmd == "config":
        config_command(remaining_argv[1:])
    elif cmd == "create_dir":
        create_dir(provider=provider_arg)
    elif cmd == "transform_photo":
        if len(remaining_argv) < 4:
            print("Usage: python3 sticker_utils.py transform_photo <photo_path> <style_preset> <output_path> [additional_description] [--provider gemini|qwen]")
            sys.exit(1)
        photo_path = remaining_argv[1]
        style_preset = remaining_argv[2]
        output_path = remaining_argv[3]
        additional_desc = remaining_argv[4] if len(remaining_argv) > 4 else ""
        prompt = build_transform_photo_prompt(style_preset, additional_desc)
        transform_photo_to_chibi(photo_path, prompt, output_path, provider=provider_arg)
    elif cmd == "draw_character":
        if len(remaining_argv) < 4:
            print("Usage: python3 sticker_utils.py draw_character <character_prompt> <style_preset> <output_path> [--provider gemini|qwen]")
            sys.exit(1)
        prompt = build_character_reference_prompt(remaining_argv[1], remaining_argv[2])
        draw_character_reference(prompt, remaining_argv[3], provider=provider_arg)
    elif cmd == "build_prompts":
        build_prompts_workspace(remaining_argv[1])
    elif cmd == "draw":
        if len(remaining_argv) < 3:
            print("Usage: python3 sticker_utils.py draw <prompt.txt> <output.png> [reference_image] [--provider gemini|qwen]")
            sys.exit(1)
        ref_image = remaining_argv[3] if len(remaining_argv) > 3 else None
        remote_draw_trigger(remaining_argv[1], remaining_argv[2], ref_image, provider=provider_arg)
    elif cmd == "draw_with_ref":
        if len(remaining_argv) < 4:
            print("Usage: python3 sticker_utils.py draw_with_ref <prompt.txt> <output.png> <reference_image> [--provider gemini|qwen]")
            sys.exit(1)
        remote_draw_trigger(remaining_argv[1], remaining_argv[2], remaining_argv[3], provider=provider_arg)
    elif cmd == "process":
        process_workspace(remaining_argv[1])
    elif cmd == "wechat_meta":
        if len(remaining_argv) < 2:
            print("Usage: python3 sticker_utils.py wechat_meta <target_dir|all> [--provider gemini|qwen]")
            sys.exit(1)
        target = remaining_argv[1]
        if target.lower() == "all":
            process_all_meta(OUTPUT_DIR, provider=provider_arg, skill_dir=SKILL_DIR)
        else:
            generate_meta(target, provider=provider_arg, skill_dir=SKILL_DIR)
