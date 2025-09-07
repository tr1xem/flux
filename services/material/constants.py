import os
import ignis
from ignis import utils


MATERIAL_CACHE_DIR = f"{ignis.CACHE_DIR}/material"  # type: ignore

TEMPLATES = utils.get_current_dir() + "/templates"
SAMPLE_WALL = utils.get_current_dir() + "../../assets/example_wallpapers/example-3.png"

os.makedirs(MATERIAL_CACHE_DIR, exist_ok=True)
