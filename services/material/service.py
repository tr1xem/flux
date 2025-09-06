import asyncio
import os

from ignis import utils
from ignis.base_service import BaseService
from ignis.css_manager import CssManager
from ignis.options import options
from jinja2 import Template
from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
from materialyoucolor.hct import Hct
from materialyoucolor.quantize import QuantizeCelebi
from materialyoucolor.scheme.scheme_content import SchemeContent
from materialyoucolor.scheme.scheme_expressive import SchemeExpressive
from materialyoucolor.scheme.scheme_fidelity import SchemeFidelity
from materialyoucolor.scheme.scheme_fruit_salad import SchemeFruitSalad
from materialyoucolor.scheme.scheme_monochrome import SchemeMonochrome
from materialyoucolor.scheme.scheme_neutral import SchemeNeutral
from materialyoucolor.scheme.scheme_rainbow import SchemeRainbow
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.scheme.scheme_vibrant import SchemeVibrant
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
        self._colors_cache = {}  # Cache for processed colors
        self._last_wallpaper_path = None
        self._last_scheme = None  
        self._last_dark_mode = None
        
        if not options.wallpaper.wallpaper_path:
            self.__on_colors_not_found()
        elif user_options.material.colors == {}:
            self.__on_colors_not_found()

        options.wallpaper.connect_option(
            "wallpaper_path", lambda: self._handle_option_change("wallpaper_path")
        )
        user_options.material.connect_option(
            "dark_mode", lambda: self._handle_option_change("dark_mode")
        )
        user_options.material.connect_option(
            "color_scheme", lambda: self._handle_option_change("color_scheme")
        )
        user_options.material.connect_option(
            "blur_enabled", lambda: self.__handle_blur_change()
        )

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring performance"""
        return {
            "colors_cache_size": len(self._colors_cache),
            "template_cache_size": len(self._template_cache),
            "last_wallpaper": self._last_wallpaper_path,
            "last_scheme": self._last_scheme,
            "last_dark_mode": self._last_dark_mode,
        }

    def _handle_option_change(self, option_name: str):
        """Handle changes to material options with caching"""
        if (
            option_name == "dark_mode"
            or option_name == "color_scheme"
            or option_name == "wallpaper_path"
        ):
            colors = self.get_colors_from_img(
                str(options.wallpaper.wallpaper_path), user_options.material.dark_mode
            )

            user_options.material.colors = colors
            css_manager.reload_all_css()
            asyncio.create_task(self.__set_matugen_scheme())
        else:
            print("Ignoring option change:", option_name)

    def __handle_blur_change(self):
        css_manager.reload_all_css()
        self.__update_hyprland_blur_config()

    def __update_hyprland_blur_config(self):
        """Add or remove blur.conf source line from hyprland.conf"""
        hyprland_conf_path = os.path.expanduser("~/.config/hypr/hyprland.conf")
        blur_conf_path = os.path.join(
            utils.get_current_dir(), "../../assets/hypr/blur.conf"
        )
        source_line = f"source={blur_conf_path}"
        if not os.path.exists(hyprland_conf_path):
            return
        try:
            with open(hyprland_conf_path, "r") as f:
                lines = f.readlines()
        except Exception:
            return

        lines = [line for line in lines if source_line not in line.strip()]
        blur_enabled = getattr(user_options.material, "blur_enabled", True)
        if blur_enabled:
            if not lines or not lines[-1].endswith("\n"):
                lines.append("\n")
            lines.append(f"{source_line}\n")

        try:
            with open(hyprland_conf_path, "w") as f:
                f.writelines(lines)
        except Exception:
            pass

    def __on_colors_not_found(self) -> None:
        options.wallpaper.set_wallpaper_path(SAMPLE_WALL)
        self.generate_colors(SAMPLE_WALL)
        asyncio.create_task(utils.exec_sh_async("hyprctl reload"))

    def get_colors_from_img(self, path: str, dark_mode: bool) -> dict[str, str]:
        """Get colors from image with caching for performance"""
        # Create cache key
        scheme_name = getattr(user_options.material, "color_scheme", "Tonal Spot")
        cache_key = f"{path}_{dark_mode}_{scheme_name}"
        
        # Return cached result if available
        if cache_key in self._colors_cache:
            return self._colors_cache[cache_key]
            
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
            scheme_class = COLOR_SCHEMES.get(scheme_name, SchemeTonalSpot)
            scheme = scheme_class(hct, dark_mode, 0.0)

            material_colors = {}
            for color in vars(MaterialDynamicColors).keys():
                color_name = getattr(MaterialDynamicColors, color)
                if hasattr(color_name, "get_hct"):
                    rgba = color_name.get_hct(scheme).to_rgba()
                    material_colors[color] = rgba_to_hex(rgba)

            # Properly close and clean up image
            image.close()
            del image_data
            del pixel_array
            
            # Cache the result before returning
            self._colors_cache[cache_key] = material_colors
            
            # Limit cache size to prevent memory bloat
            if len(self._colors_cache) > 50:
                # Remove oldest entries
                oldest_keys = list(self._colors_cache.keys())[:-25]
                for key in oldest_keys:
                    del self._colors_cache[key]
            
            return material_colors
        except Exception as e:
            print(f"Error generating colors from {path}: {e}")
            self.__on_colors_not_found()
            return {}

    def generate_colors(self, path: str) -> None:
        colors = self.get_colors_from_img(path, user_options.material.dark_mode)
        dark_colors = self.get_colors_from_img(path, True)
        user_options.material.colors = colors
        self.__render_templates(colors, dark_colors)
        asyncio.create_task(self.__setup(path))

    def __render_templates(self, colors: dict, dark_colors: dict) -> None:
        for template in os.listdir(TEMPLATES):
            self.render_template(
                colors=colors,
                dark_mode=user_options.material.dark_mode,
                input_file=f"{TEMPLATES}/{template}",
                output_file=f"{MATERIAL_CACHE_DIR}/{template}",
            )

        for template in os.listdir(TEMPLATES):
            self.render_template(
                colors=dark_colors,
                dark_mode=True,
                input_file=f"{TEMPLATES}/{template}",
                output_file=f"{MATERIAL_CACHE_DIR}/dark_{template}",
            )

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
        # await self.__reload_gtk_theme()

    async def __set_matugen_scheme(self) -> None:
        asyncio.create_task(
            utils.exec_sh_async(
                f"/usr/bin/matugen image -t {user_options.material.color_scheme} {options.wallpaper.wallpaper_path}"
            )
        )
