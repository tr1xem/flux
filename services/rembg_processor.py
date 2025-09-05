import argparse
import sys
from pathlib import Path

from rembg import new_session, remove


def process_image_rembg(
    input_path_str: str,
    output_path_str: str,
    model_name: str,
    alpha_matting: bool,
    foreground_threshold: int,
    background_threshold: int,
    erode_size: int,
):
    input_path = Path(input_path_str)
    output_path = Path(output_path_str)

    if not input_path.is_file():
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        session = new_session(model_name)

        with open(input_path, "rb") as i:
            input_data = i.read()

            output_data = remove(
                input_data,
                session=session,
                alpha_matting=alpha_matting,
                alpha_matting_foreground_threshold=foreground_threshold,
                alpha_matting_background_threshold=background_threshold,
                alpha_matting_erode_size=erode_size,
            )

            with open(output_path, "wb") as o:
                o.write(output_data)

        print(
            f"Success (rembg model: '{model_name}', alpha_matting: {alpha_matting}): "
            f"Foreground created at '{output_path}'"
        )

    except Exception as e:
        print(f"An error occurred in rembg script: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    """
    Full usage
    python create_depth_image_rembg.py /path/to/input.jpg /path/to/output.png --alpha-matting --foreground-threshold 200 --erode-size 5
    """

    parser = argparse.ArgumentParser(
        description="Remove background from an image using rembg."
    )

    parser.add_argument("input_path", help="Path to the input image file.")
    parser.add_argument("output_path", help="Path to save the output PNG file.")

    parser.add_argument(
        "-m",
        "--model",
        choices=["u2net", "isnet-general-use"],
        default="u2net",
        help="The model to use for background removal. Default is 'u2net'.",
    )
    parser.add_argument(
        "-a",
        "--alpha-matting",
        action="store_true",
        help="Enable alpha matting for finer edge detail.",
    )

    parser.add_argument(
        "-ft",
        "--foreground-threshold",
        type=int,
        default=240,
        help="Foreground threshold for alpha matting. Default is 240.",
    )
    parser.add_argument(
        "-bt",
        "--background-threshold",
        type=int,
        default=10,
        help="Background threshold for alpha matting. Default is 10.",
    )
    parser.add_argument(
        "-e",
        "--erode-size",
        type=int,
        default=15,
        help="Erode size for alpha matting. Default is 15.",
    )

    args = parser.parse_args()

    process_image_rembg(
        args.input_path,
        args.output_path,
        args.model,
        args.alpha_matting,
        args.foreground_threshold,
        args.background_threshold,
        args.erode_size,
    )
