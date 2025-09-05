import os
import hashlib
from pathlib import Path
from PIL import Image
from ignis import utils, CACHE_DIR
from user_options import user_options


def get_monitor_size():
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
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def process_wallpaper_with_rembg(wallpaper_path):
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