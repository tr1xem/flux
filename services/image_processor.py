import hashlib
import os
import tempfile

from ignis import utils
from PIL import Image


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


def scale_to_fit(
    image_path: str,
    target_width: int,
    target_height: int,
    resampling=Image.Resampling.LANCZOS,
) -> str:
    """
    Scale an image to fit within target dimensions while preserving aspect ratio.
    Returns path to scaled image, or original path if scaling fails/not needed.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path

    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size

            original_aspect = original_width / original_height
            target_aspect = target_width / target_height

            if original_aspect > target_aspect:
                new_width = target_width
                new_height = int(target_width / original_aspect)
            else:
                new_height = target_height
                new_width = int(target_height * original_aspect)

            if new_width < original_width or new_height < original_height:
                scaled_img = img.resize((new_width, new_height), resampling)

                temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(temp_fd)
                scaled_img.save(temp_path, "PNG", optimize=True)

                return temp_path
            else:
                return image_path

    except Exception as e:
        print(f"Error scaling image {image_path}: {e}")
        return image_path


def crop_to_square(image_path: str) -> str:
    """
    Crop an image to square aspect ratio (center crop).
    Returns path to cropped image, or original path if cropping fails/not needed.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path

    try:
        with Image.open(image_path) as img:
            width, height = img.size

            if width == height:
                return image_path

            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size

            cropped = img.crop((left, top, right, bottom))

            temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(temp_fd)
            cropped.save(temp_path, "PNG")

            return temp_path

    except Exception as e:
        print(f"Error cropping image {image_path}: {e}")
        return image_path


def scale_to_screen_resolution(image_path: str) -> str:
    """
    Scale an image to fit screen resolution while preserving aspect ratio.
    Convenience function for wallpaper processing.
    """
    screen_width, screen_height = get_monitor_size()
    return scale_to_fit(image_path, screen_width, screen_height)


def scale_for_preview(
    image_path: str, target_width: int = 480, target_height: int = 270
) -> str:
    """
    Scale an image for preview display (default 480x270).
    Convenience function for appearance preview.
    """
    return scale_to_fit(image_path, target_width, target_height)


def get_image_hash(image_path: str) -> str:
    """Get MD5 hash of an image file for caching purposes"""
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def create_cached_image(
    image_path: str, cache_dir: str, filename_prefix: str, processor_func, *args
) -> str:
    """
    Create a cached processed image using the given processor function.
    Returns path to cached image or processes and caches if not exists.
    """
    if not image_path or not os.path.exists(image_path):
        return image_path

    os.makedirs(cache_dir, exist_ok=True)

    image_hash = get_image_hash(image_path)
    if not image_hash:
        return image_path

    cached_filename = f"{filename_prefix}_{image_hash}.png"
    cached_path = os.path.join(cache_dir, cached_filename)

    if os.path.exists(cached_path):
        return cached_path

    try:
        processed_path = processor_func(image_path, *args)

        if processed_path != image_path and os.path.exists(processed_path):
            os.rename(processed_path, cached_path)
            return cached_path
        else:
            return processed_path

    except Exception as e:
        print(f"Error creating cached image: {e}")
        return image_path

