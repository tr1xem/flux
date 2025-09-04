#!/usr/bin/python
import asyncio
import gc
import hashlib
import os
from typing import Optional

from gi.repository import GLib  # type: ignore
from ignis import utils
from ignis.base_service import BaseService
from ignis.css_manager import CssManager
from ignis.options import options
from jinja2 import Template
from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.quantize import QuantizeCelebi
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.scheme.scheme_expressive import SchemeExpressive
from materialyoucolor.scheme.scheme_neutral import SchemeNeutral
from materialyoucolor.scheme.scheme_vibrant import SchemeVibrant
from materialyoucolor.scheme.scheme_fidelity import SchemeFidelity
from materialyoucolor.scheme.scheme_monochrome import SchemeMonochrome
from materialyoucolor.scheme.scheme_content import SchemeContent
from materialyoucolor.scheme.scheme_rainbow import SchemeRainbow
from materialyoucolor.scheme.scheme_fruit_salad import SchemeFruitSalad
from materialyoucolor.score.score import Score
from PIL import Image

from user_options import user_options

from .constants import MATERIAL_CACHE_DIR, SAMPLE_WALL, TEMPLATES
from .util import calculate_optimal_size, rgba_to_hex

css_manager = CssManager.get_default()

# Color scheme mappings
COLOR_SCHEMES = {
    "Tonal Spot": SchemeTonalSpot,
    "Expressive": SchemeExpressive,
    "Neutral": SchemeNeutral,
    "Vibrant": SchemeVibrant,
    "Fidelity": SchemeFidelity,
    "Monochrome": SchemeMonochrome,
    "Content": SchemeContent,
    "Rainbow": SchemeRainbow,
    "Fruit Salad": SchemeFruitSalad,
}


class MaterialService(BaseService):
    def __init__(self):
        super().__init__()
        
        # Caching mechanisms
        self._colors_cache = {}
        self._template_cache = {}
        self._last_wallpaper_path = None
        self._last_scheme = None
        self._last_dark_mode = None
        
        # Initialize only if necessary
        if not options.wallpaper.wallpaper_path:
            self.__on_colors_not_found()
        elif user_options.material.colors == {}:
            self.__on_colors_not_found()

        user_options.material.connect_option(
            "dark_mode", lambda: self._handle_option_change("dark_mode")
        )
        user_options.material.connect_option(
            "color_scheme", lambda: self._handle_option_change("color_scheme")
        )
        user_options.material.connect_option(
            "blur_enabled", lambda: self.__handle_blur_change()
        )
        
        # Apply initial blur state
        self.__handle_blur_change()

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring performance"""
        return {
            "colors_cache_size": len(self._colors_cache),
            "template_cache_size": len(self._template_cache),
            "last_wallpaper": self._last_wallpaper_path,
            "last_scheme": self._last_scheme,
            "last_dark_mode": self._last_dark_mode
        }

    def _cleanup_cache(self, max_entries: int = 10):
        """Clean up caches to prevent memory leaks"""
        if len(self._colors_cache) > max_entries:
            # Keep only the most recent entries
            items = list(self._colors_cache.items())
            self._colors_cache = dict(items[-max_entries//2:])
            
        if len(self._template_cache) > max_entries:
            # Keep only the most recent entries  
            items = list(self._template_cache.items())
            self._template_cache = dict(items[-max_entries//2:])

    def _handle_option_change(self, option_name: str):
        """Handle changes to material options with caching"""
        current_path = options.wallpaper.wallpaper_path
        if current_path:
            # Clear cache if relevant options changed
            if (self._last_wallpaper_path != current_path or 
                self._last_scheme != user_options.material.color_scheme or
                self._last_dark_mode != user_options.material.dark_mode):
                # Only clear caches, don't regenerate immediately
                self._colors_cache.clear()
                self._template_cache.clear()
                
            self.generate_colors(current_path)
            
            # Cleanup caches after each change to prevent accumulation
            self._cleanup_cache(max_entries=8)

    def _get_cache_key(self, path: str, dark_mode: bool) -> str:
        """Generate a cache key for color calculations"""
        # Include file modification time for cache invalidation
        try:
            mtime = os.path.getmtime(path)
            scheme = user_options.material.color_scheme
            return hashlib.md5(f"{path}_{dark_mode}_{scheme}_{mtime}".encode()).hexdigest()
        except OSError:
            # If file doesn't exist, use path + timestamp
            return hashlib.md5(f"{path}_{dark_mode}_{user_options.material.color_scheme}".encode()).hexdigest()

    def __handle_blur_change(self):
        """Handle blur setting changes - update CSS and Hyprland config"""
        css_manager.reload_all_css()
        self.__update_hyprland_blur_config()

    def __update_hyprland_blur_config(self):
        """Add or remove blur.conf source line from hyprland.conf"""
        hyprland_conf_path = os.path.expanduser("~/.config/hypr/hyprland.conf")
        
        # Get path to blur.conf relative to config.py location
        config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # Go up from services/material/ to ignis root
        blur_conf_path = os.path.join(config_dir, "assets/hypr/blur.conf")
        source_line = f"source={blur_conf_path}"
        
        # Check if hyprland.conf exists
        if not os.path.exists(hyprland_conf_path):
            return
            
        # Read current content
        try:
            with open(hyprland_conf_path, 'r') as f:
                lines = f.readlines()
        except Exception:
            return
            
        # Remove existing source line if present
        lines = [line for line in lines if source_line not in line.strip()]
        
        # Add source line if blur is enabled
        blur_enabled = getattr(user_options.material, 'blur_enabled', True)
        if blur_enabled:
            # Add source line at the end
            if not lines or not lines[-1].endswith('\n'):
                lines.append('\n')
            lines.append(f"{source_line}\n")
        
        # Write back to file
        try:
            with open(hyprland_conf_path, 'w') as f:
                f.writelines(lines)
        except Exception:
            pass

    def __on_colors_not_found(self) -> None:
        options.wallpaper.set_wallpaper_path(SAMPLE_WALL)
        self.generate_colors(SAMPLE_WALL)
        asyncio.create_task(utils.exec_sh_async("hyprctl reload"))

    def get_colors_from_img(self, path: str, dark_mode: bool) -> dict[str, str]:
        """Get colors from image with caching for performance"""
        cache_key = self._get_cache_key(path, dark_mode)
        
        # Return cached result if available
        if cache_key in self._colors_cache:
            return self._colors_cache[cache_key]

        # Generate colors if not cached
        image = None
        try:
            image = Image.open(path)
            wsize, hsize = image.size
            wsize_new, hsize_new = calculate_optimal_size(wsize, hsize, 128)
            if wsize_new < wsize or hsize_new < hsize:
                image = image.resize((wsize_new, hsize_new), Image.Resampling.BICUBIC)  # type: ignore

            pixel_len = image.width * image.height
            image_data = image.getdata()
            pixel_array = [image_data[_] for _ in range(0, pixel_len, 1)]

            colors = QuantizeCelebi(pixel_array, 128)
            argb = Score.score(colors)[0]

            hct = Hct.from_int(argb)
            
            # Get the selected color scheme class
            scheme_name = getattr(user_options.material, 'color_scheme', 'Tonal Spot')
            scheme_class = COLOR_SCHEMES.get(scheme_name, SchemeTonalSpot)
            scheme = scheme_class(hct, dark_mode, 0.0)

            material_colors = {}
            for color in vars(MaterialDynamicColors).keys():
                color_name = getattr(MaterialDynamicColors, color)
                if hasattr(color_name, "get_hct"):
                    rgba = color_name.get_hct(scheme).to_rgba()
                    material_colors[color] = rgba_to_hex(rgba)

            # Cache the result
            self._colors_cache[cache_key] = material_colors
            
            # Update tracking variables
            self._last_wallpaper_path = path
            self._last_scheme = scheme_name
            self._last_dark_mode = dark_mode

            return material_colors
        except Exception as e:
            print(f"Error generating colors from {path}: {e}")
            # Return empty colors on error
            return {}
        finally:
            # Always close the PIL Image to prevent memory leaks
            if image is not None:
                try:
                    image.close()
                except Exception:
                    pass

    def generate_colors(self, path: str) -> None:
        """Generate colors with optimized caching and lazy loading"""
        if not path:
            return
            
        # Check if we need to regenerate colors
        current_scheme = user_options.material.color_scheme
        current_dark_mode = user_options.material.dark_mode
        
        # Skip if nothing changed and colors exist
        if (self._last_wallpaper_path == path and 
            self._last_scheme == current_scheme and 
            self._last_dark_mode == current_dark_mode and
            user_options.material.colors):
            return

        colors = self.get_colors_from_img(path, current_dark_mode)
        dark_colors = self.get_colors_from_img(path, True)
        
        user_options.material.colors = colors
        self.__render_templates(colors, dark_colors)
        asyncio.create_task(self.__setup(path))

    def __render_templates(self, colors: dict, dark_colors: dict) -> None:
        """Render templates with caching optimization"""
        # Generate cache keys for colors
        colors_hash = hashlib.md5(str(sorted(colors.items())).encode()).hexdigest()
        dark_colors_hash = hashlib.md5(str(sorted(dark_colors.items())).encode()).hexdigest()
        
        for template in os.listdir(TEMPLATES):
            # Check cache for regular template
            cache_key = f"{template}_{colors_hash}_{user_options.material.dark_mode}"
            if cache_key not in self._template_cache:
                self.render_template(
                    colors=colors,
                    dark_mode=user_options.material.dark_mode,
                    input_file=f"{TEMPLATES}/{template}",
                    output_file=f"{MATERIAL_CACHE_DIR}/{template}",
                )
                self._template_cache[cache_key] = True
            
            # Check cache for dark template
            dark_cache_key = f"dark_{template}_{dark_colors_hash}_True"
            if dark_cache_key not in self._template_cache:
                self.render_template(
                    colors=dark_colors,
                    dark_mode=True,
                    input_file=f"{TEMPLATES}/{template}",
                    output_file=f"{MATERIAL_CACHE_DIR}/dark_{template}",
                )
                self._template_cache[dark_cache_key] = True
        
        # Clean up template cache after each render to prevent memory leaks
        self._cleanup_cache(max_entries=12)

    def render_template(
        self,
        colors: dict,
        input_file: str,
        output_file: str,
        dark_mode: bool | None = None,
    ) -> None:
        if dark_mode is None:
            colors["dark_mode"] = str(user_options.material.dark_mode).lower()
        else:
            colors["dark_mode"] = str(dark_mode).lower()
        
        with open(input_file) as file:
            template_rendered = Template(file.read()).render(colors)

        with open(output_file, "w") as file:
            file.write(template_rendered)

    async def __reload_gtk_theme(self) -> None:
        THEME_CMD = "gsettings set org.gnome.desktop.interface gtk-theme {}"
        COLOR_SCHEME_CMD = "gsettings set org.gnome.desktop.interface color-scheme {}"
        await utils.exec_sh_async(THEME_CMD.format("Adwaita"))
        await utils.exec_sh_async(THEME_CMD.format("Material"))
        await utils.exec_sh_async(COLOR_SCHEME_CMD.format("default"))
        await utils.exec_sh_async(COLOR_SCHEME_CMD.format("prefer-dark"))
        await utils.exec_sh_async(COLOR_SCHEME_CMD.format("default"))

    async def __setup(self, image_path: str) -> None:
        try:
            await utils.exec_sh_async("pkill -SIGUSR1 kitty")
        except Exception:
            ...
        options.wallpaper.set_wallpaper_path(image_path)
        css_manager.reload_all_css()
        
        # Force garbage collection after color changes to free memory
        gc.collect()
        # await self.__reload_gtk_theme()
