from plyfile import PlyData
import numpy as np
import argparse
from io import BytesIO
import os
import sys


def process_ply_to_splat(ply_file_path):
    try:
        print(f"Reading PLY file from: {ply_file_path}")
        plydata = PlyData.read(ply_file_path)
        vert = plydata["vertex"]
        
        # Sort points by size and opacity for better rendering
        sorted_indices = np.argsort(
            -np.exp(vert["scale_0"] + vert["scale_1"] + vert["scale_2"])
            / (1 + np.exp(-vert["opacity"]))
        )
        
        buffer = BytesIO()
        for idx in sorted_indices:
            v = plydata["vertex"][idx]
            position = np.array([v["x"], v["y"], v["z"]], dtype=np.float32)
            scales = np.exp(
                np.array(
                    [v["scale_0"], v["scale_1"], v["scale_2"]],
                    dtype=np.float32,
                )
            )
            rot = np.array(
                [v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]],
                dtype=np.float32,
            )
            SH_C0 = 0.28209479177387814
            color = np.array(
                [
                    0.5 + SH_C0 * v["f_dc_0"],
                    0.5 + SH_C0 * v["f_dc_1"],
                    0.5 + SH_C0 * v["f_dc_2"],
                    1 / (1 + np.exp(-v["opacity"])),
                ]
            )
            buffer.write(position.tobytes())
            buffer.write(scales.tobytes())
            buffer.write((color * 255).clip(0, 255).astype(np.uint8).tobytes())
            buffer.write(
                ((rot / np.linalg.norm(rot)) * 128 + 128)
                .clip(0, 255)
                .astype(np.uint8)
                .tobytes()
            )
        
        print(f"Successfully processed PLY data with {len(sorted_indices)} points")
        return buffer.getvalue()
    except Exception as e:
        print(f"Error processing PLY file: {e}")
        return None


def save_splat_file(splat_data, output_path):
    try:
        with open(output_path, "wb") as f:
            f.write(splat_data)
        print(f"Successfully saved SPLAT file to: {output_path}")
        return True
    except Exception as e:
        print(f"Error saving SPLAT file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Convert PLY files to SPLAT format.")
    parser.add_argument(
        "input_file", help="The input PLY file to process."
    )
    parser.add_argument(
        "output_file", help="The output SPLAT file path."
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file {args.input_file} does not exist.")
        sys.exit(1)
    
    print(f"Converting {args.input_file} to {args.output_file}...")
    splat_data = process_ply_to_splat(args.input_file)
    
    if splat_data:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(args.output_file)), exist_ok=True)
        
        if save_splat_file(splat_data, args.output_file):
            print(f"Conversion successful: {args.output_file}")
            sys.exit(0)
        else:
            print("Failed to save SPLAT file")
            sys.exit(1)
    else:
        print("PLY conversion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()