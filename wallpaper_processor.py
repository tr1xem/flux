import os
import asyncio
import hashlib
from pathlib import Path
from PIL import Image
from ignis import utils, CACHE_DIR
from ignis.options import options
from user_options import user_options


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
        with open(image_path, 'rb') as f:
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

    image_hash = await get_image_hash_async(wallpaper_path)
    screen_width, screen_height = get_monitor_size()

    output_filename = f"depth_wall_{image_hash}_{screen_width}x{screen_height}.png"
    output_path = os.path.join(wallpaper_cache_dir, output_filename)

    print(f"Processing wallpaper: {wallpaper_path} -> {output_path}")

    if os.path.exists(output_path):
        print(f"Using cached depth wall: {output_path}")
        user_options.wallpaper.depth_wall = output_path
        return output_path

    temp_scaled_path = os.path.join(
        wallpaper_cache_dir, f"temp_scaled_{image_hash}.png"
    )

    try:

        def _downscale_wallpaper():
            print("Downscaling wallpaper before background removal...")
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
            return True

        async def _remove_background():
            print("Removing background from downscaled image...")
            rem_script = os.path.join(utils.get_current_dir(), "rem.py")
            cmd = f"python {rem_script} -m u2net {temp_scaled_path} {output_path}"

            result = await utils.exec_sh_async(cmd)
            print(f"Background removal completed: {result.stdout}")
            return True

        loop = asyncio.get_event_loop()

        # Downscale wallpaper first (much faster for background removal)
        await loop.run_in_executor(None, _downscale_wallpaper)
        print(f"Wallpaper downscaled to {screen_width}x{screen_height}")

        # Remove background from downscaled image
        await _remove_background()
        print("Background removal completed")

        # Clean up temp scaled file
        if os.path.exists(temp_scaled_path):
            os.remove(temp_scaled_path)

        user_options.wallpaper.depth_wall = output_path
        print(f"Processed wallpaper saved and set: {output_path}")
        return output_path

    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        import traceback

        traceback.print_exc()
        # Clean up temp file if it exists
        if os.path.exists(temp_scaled_path):
            os.remove(temp_scaled_path)
        return None


# Track original wallpaper paths to avoid processing loops
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

    image_hash = await get_image_hash_async(original_wallpaper_path)
    screen_width, screen_height = get_monitor_size()

    output_filename = f"wallpaper_{image_hash}_{screen_width}x{screen_height}.png"
    output_path = os.path.join(wallpaper_cache_dir, output_filename)

    print(f"Downscaling wallpaper: {original_wallpaper_path} -> {output_path}")

    if os.path.exists(output_path):
        print(f"Using cached downscaled wallpaper: {output_path}")
        # Set the downscaled wallpaper as the active wallpaper
        _processing_wallpaper = True
        options.wallpaper.set_wallpaper_path(output_path)
        _processing_wallpaper = False
        return output_path

    try:

        def _downscale():
            print("Downscaling wallpaper to screen resolution...")
            with Image.open(original_wallpaper_path) as img:
                img_ratio = img.width / img.height
                screen_ratio = screen_width / screen_height

                # Only downscale if image is larger than screen resolution
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
                    # If image is already small enough, just copy it
                    img.save(output_path)
                    print("Wallpaper size is already optimal")
            return True

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _downscale)

        # Set the downscaled wallpaper as the active wallpaper
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
            # Check if this is a new original wallpaper (not our processed version)
            if not wallpaper_path.startswith(CACHE_DIR):
                _original_wallpaper_path = wallpaper_path
                print(f"New wallpaper detected, processing: {wallpaper_path}")
                # Downscale wallpaper for better performance
                asyncio.create_task(downscale_wallpaper_async(wallpaper_path))

            # Process for depth wall if enabled (use original path)
            if user_options.wallpaper.depth_wall_enabled and _original_wallpaper_path:
                asyncio.create_task(
                    process_wallpaper_with_rembg_async(_original_wallpaper_path)
                )
        else:
            # Clear paths when no wallpaper
            _original_wallpaper_path = None
            user_options.wallpaper.depth_wall = ""
    except Exception as e:
        print(f"Error processing wallpaper: {e}")


def on_depth_wall_toggle():
    try:
        if user_options.wallpaper.depth_wall_enabled:
            # Process current wallpaper when enabled
            wallpaper_path = options.wallpaper.wallpaper_path
            if wallpaper_path:
                print("Depth wall enabled, processing...")
                asyncio.create_task(process_wallpaper_with_rembg_async(wallpaper_path))
        else:
            # Clear path when disabled
            print("Depth wall disabled, clearing path...")
            user_options.wallpaper.depth_wall = ""
    except Exception as e:
        print(f"Error toggling depth wall: {e}")


def process_wallpaper_with_rembg(wallpaper_path):
    """Synchronous version for backwards compatibility"""
    if not wallpaper_path or not os.path.exists(wallpaper_path):
        return None
    
    wallpaper_cache_dir = os.path.join(CACHE_DIR, "wallpapers")
    os.makedirs(wallpaper_cache_dir, exist_ok=True)
    
    image_hash = get_image_hash(wallpaper_path)
    screen_width, screen_height = get_monitor_size()
    
    output_filename = f"depth_wall_{image_hash}_{screen_width}x{screen_height}.png"
    output_path = os.path.join(wallpaper_cache_dir, output_filename)
    
    if os.path.exists(output_path):
        user_options.wallpaper.depth_wall = output_path
        return output_path
    
    temp_scaled_path = os.path.join(wallpaper_cache_dir, f"temp_scaled_{image_hash}.png")
    temp_rembg_path = os.path.join(wallpaper_cache_dir, f"temp_rembg_{image_hash}.png")
    
    try:
        # First, downscale the wallpaper to screen resolution for faster processing
        print("Downscaling wallpaper...")
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
        rem_script = os.path.join(utils.get_current_dir(), "rem.py")
        cmd = f"python {rem_script} -m u2net {temp_scaled_path} {temp_rembg_path}"
        
        result = utils.exec_sh(cmd)
        print(f"Background removal completed: {result.stdout}")
        
        # Move the processed image to final output path
        os.rename(temp_rembg_path, output_path)
        
        # Clean up temp scaled file
        os.remove(temp_scaled_path)
        
        user_options.wallpaper.depth_wall = output_path
        print(f"Processed wallpaper saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing wallpaper: {e}")
        # Clean up temp files
        for temp_file in [temp_scaled_path, temp_rembg_path]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return None