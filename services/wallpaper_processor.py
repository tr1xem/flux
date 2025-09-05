import asyncio
import hashlib
import os

from ignis import CACHE_DIR, utils
from ignis.options import options
from PIL import Image

from user_options import user_options
# NOTE: I m using external script for rembg, because in that way i dont have to care about handeling memory pro move btw


def get_monitor_size():
    """Get the monitor dimensions, with fallback to 1920x1080"""
    try:
        monitor = utils.get_monitor(0)
        if monitor:
            geometry = monitor.get_geometry()
            if geometry:
                return geometry.width, geometry.height
        return 1920, 1080
    except Exception:
        return 1920, 1080


def get_image_hash(image_path):
    """Get MD5 hash of an image file for caching purposes"""
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


async def get_image_hash_async(image_path):
    def _get_hash():
        return get_image_hash(image_path)

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_hash)


async def process_wallpaper_with_rembg_async(wallpaper_path):
    if not wallpaper_path or not os.path.exists(wallpaper_path):
        print(f"Wallpaper path invalid: {wallpaper_path}")
        return None

    wallpaper_cache_dir = os.path.join(CACHE_DIR, "wallpapers")
    os.makedirs(wallpaper_cache_dir, exist_ok=True)

    output_path = os.path.join(wallpaper_cache_dir, "wallpaper_depth.png")
    temp_scaled_path = os.path.join(wallpaper_cache_dir, "temp_scaled.png")

    print(f"Processing wallpaper: {wallpaper_path} -> {output_path}")

    try:

        def _downscale_wallpaper():
            print("Downscaling wallpaper before background removal...")
            screen_width, screen_height = get_monitor_size()
            with Image.open(wallpaper_path) as img:
                img_ratio = img.width / img.height
                screen_ratio = screen_width / screen_height

                if img_ratio > screen_ratio:
                    new_width = screen_width
                    new_height = int(screen_width / img_ratio)
                else:
                    new_height = screen_height
                    new_width = int(screen_height * img_ratio)

                scaled_img = img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )
                scaled_img.save(temp_scaled_path)
                print(f"Temp file saved: {temp_scaled_path}")
            return True

        def _remove_background():
            print("Removing background from downscaled image...")

            script_dir = os.path.dirname(os.path.abspath(__file__))
            rem_script = os.path.join(script_dir, "rembg_processor.py")
            cmd = f'python "{rem_script}" -m u2net --alpha-matting "{temp_scaled_path}" "{output_path}"'
            print(f"Running command: {cmd}")

            result = utils.exec_sh(cmd)
            print(f"Background removal result: {result.returncode}")
            print(f"Background removal stdout: {result.stdout}")
            print(f"Background removal stderr: {result.stderr}")
            return result.returncode == 0

        loop = asyncio.get_event_loop()

        await loop.run_in_executor(None, _downscale_wallpaper)
        screen_width, screen_height = get_monitor_size()
        print(f"Wallpaper downscaled to {screen_width}x{screen_height}")

        if not os.path.exists(temp_scaled_path):
            print(f"Error: Temp file not found: {temp_scaled_path}")
            return None

        success = await loop.run_in_executor(None, _remove_background)

        if not success:
            print("Background removal failed")
            return None

        if not os.path.exists(output_path):
            print(f"Error: Output file not created: {output_path}")
            return None

        print("Background removal completed")

        if os.path.exists(temp_scaled_path):
            os.remove(temp_scaled_path)
            print("Temp file cleaned up")

        user_options.wallpaper.depth_wall = output_path
        print(f"Processed wallpaper saved and set: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        import traceback

        traceback.print_exc()

        if os.path.exists(temp_scaled_path):
            os.remove(temp_scaled_path)
        return None


_original_wallpaper_path = None
_processing_wallpaper = False


async def downscale_wallpaper_async(original_wallpaper_path):
    """Downscale wallpaper to screen resolution for better performance"""
    global _processing_wallpaper

    if _processing_wallpaper:
        return None

    if not original_wallpaper_path or not os.path.exists(original_wallpaper_path):
        print(f"Wallpaper path invalid: {original_wallpaper_path}")
        return None

    wallpaper_cache_dir = os.path.join(CACHE_DIR, "wallpapers")
    os.makedirs(wallpaper_cache_dir, exist_ok=True)

    output_path = os.path.join(wallpaper_cache_dir, "wallpaper.png")

    print(f"Downscaling wallpaper: {original_wallpaper_path} -> {output_path}")

    try:

        def _downscale():
            print("Downscaling wallpaper to screen resolution...")
            screen_width, screen_height = get_monitor_size()
            with Image.open(original_wallpaper_path) as img:
                img_ratio = img.width / img.height
                screen_ratio = screen_width / screen_height

                if img.width > screen_width or img.height > screen_height:
                    if img_ratio > screen_ratio:
                        new_width = screen_width
                        new_height = int(screen_width / img_ratio)
                    else:
                        new_height = screen_height
                        new_width = int(screen_height * img_ratio)

                    scaled_img = img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS
                    )
                    scaled_img.save(output_path)
                    print(f"Wallpaper downscaled to {new_width}x{new_height}")
                else:
                    img.save(output_path)
                    print("Wallpaper size is already optimal")
            return True

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _downscale)

        _processing_wallpaper = True
        options.wallpaper.set_wallpaper_path(output_path)
        _processing_wallpaper = False
        print(f"Wallpaper set to downscaled version: {output_path}")

        return output_path

    except Exception as e:
        print(f"Error downscaling wallpaper: {e}")
        _processing_wallpaper = False
        import traceback

        traceback.print_exc()
        return None


def on_wallpaper_change():
    global _original_wallpaper_path, _processing_wallpaper

    if _processing_wallpaper:
        return

    try:
        wallpaper_path = options.wallpaper.wallpaper_path
        if wallpaper_path:
            if not wallpaper_path.startswith(CACHE_DIR):
                _original_wallpaper_path = wallpaper_path
                print(f"New wallpaper detected, processing: {wallpaper_path}")

                asyncio.create_task(downscale_wallpaper_async(wallpaper_path))

            if user_options.wallpaper.depth_wall_enabled and _original_wallpaper_path:
                asyncio.create_task(
                    process_wallpaper_with_rembg_async(_original_wallpaper_path)
                )
        else:
            _original_wallpaper_path = None
            user_options.wallpaper.depth_wall = ""
    except Exception as e:
        print(f"Error processing wallpaper: {e}")


def on_depth_wall_toggle():
    try:
        if user_options.wallpaper.depth_wall_enabled:
            wallpaper_cache_dir = os.path.join(CACHE_DIR, "wallpapers")
            depth_path = os.path.join(wallpaper_cache_dir, "wallpaper_depth.png")

            if os.path.exists(depth_path):
                print(f"Using existing depth wall: {depth_path}")
                user_options.wallpaper.depth_wall = depth_path
            else:
                wallpaper_path = options.wallpaper.wallpaper_path
                if wallpaper_path:
                    print("Depth wall enabled, processing...")
                    asyncio.create_task(
                        process_wallpaper_with_rembg_async(
                            _original_wallpaper_path or wallpaper_path
                        )
                    )

    except Exception as e:
        print(f"Error toggling depth wall: {e}")


def process_wallpaper_with_rembg(wallpaper_path):
    """Synchronous version for backwards compatibility"""
    if not wallpaper_path or not os.path.exists(wallpaper_path):
        return None

    wallpaper_cache_dir = os.path.join(CACHE_DIR, "wallpapers")
    os.makedirs(wallpaper_cache_dir, exist_ok=True)

    output_path = os.path.join(wallpaper_cache_dir, "wallpaper_depth.png")
    temp_scaled_path = os.path.join(wallpaper_cache_dir, "temp_scaled.png")
    temp_rembg_path = os.path.join(wallpaper_cache_dir, "temp_rembg.png")

    try:
        print("Downscaling wallpaper...")
        screen_width, screen_height = get_monitor_size()
        with Image.open(wallpaper_path) as img:
            img_ratio = img.width / img.height
            screen_ratio = screen_width / screen_height

            if img_ratio > screen_ratio:
                new_width = screen_width
                new_height = int(screen_width / img_ratio)
            else:
                new_height = screen_height
                new_width = int(screen_height * img_ratio)

            scaled_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            scaled_img.save(temp_scaled_path)

        print("Downscaling completed, starting background removal...")
        rem_script = os.path.join(
            utils.get_current_dir(), "services", "rembg_processor.py"
        )
        cmd = f"python {rem_script} -m u2net {temp_scaled_path} {temp_rembg_path}"

        result = utils.exec_sh(cmd)
        print(f"Background removal completed: {result.stdout}")

        os.rename(temp_rembg_path, output_path)

        os.remove(temp_scaled_path)

        user_options.wallpaper.depth_wall = output_path
        print(f"Processed wallpaper saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error processing wallpaper: {e}")

        for temp_file in [temp_scaled_path, temp_rembg_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None
