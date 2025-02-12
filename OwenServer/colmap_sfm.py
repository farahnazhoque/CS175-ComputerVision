import os
import subprocess
import argparse
import platform
import sys

def run_colmap_pipeline():
    parser = argparse.ArgumentParser(description="Full COLMAP reconstruction pipeline")
    parser.add_argument('--input', required=True, help="Path to input frames folder")
    parser.add_argument('--output', required=True, help="Path to output COLMAP folder")
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    args = parser.parse_args()

    # Path setup
    database_path = os.path.join(args.output, 'database.db')
    sparse_dir = os.path.join(args.output, 'sparse')
    dense_dir = os.path.join(args.output, 'dense')
    text_dir = os.path.join(args.output, 'text')
    vocab_tree_path = os.path.join(os.path.dirname(__file__), 'vocab_tree_flickr100K_words32K.bin')

    # Create directories
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(dense_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)

    # Get COLMAP executable
    system = platform.system().lower()
    colmap_exec = 'COLMAP.bat' if system == 'windows' else 'colmap'
    if not os.path.exists(colmap_exec):
        raise FileNotFoundError(f"COLMAP executable not found at {colmap_exec}")

    try:
        # Feature extraction
        subprocess.run([
            colmap_exec, 'feature_extractor',
            '--database_path', database_path,
            '--image_path', args.input,
            '--ImageReader.camera_model', 'SIMPLE_PINHOLE',
            '--ImageReader.camera_params', f"{max(args.width, args.height) * 0.8},{args.width/2},{args.height/2}",
            '--SiftExtraction.max_image_size', str(max(args.width, args.height))
        ], check=True)

        # Feature matching
        subprocess.run([
            colmap_exec, 'vocab_tree_matcher',
            '--database_path', database_path,
            '--VocabTreeMatching.vocab_tree_path', vocab_tree_path
        ], check=True)

        # Sparse reconstruction
        subprocess.run([
            colmap_exec, 'mapper',
            '--database_path', database_path,
            '--image_path', args.input,
            '--output_path', sparse_dir
        ], check=True)

        # Dense reconstruction
        subprocess.run([
            colmap_exec, 'image_undistorter',
            '--image_path', args.input,
            '--input_path', os.path.join(sparse_dir, '0'),
            '--output_path', dense_dir
        ], check=True)

        subprocess.run([
            colmap_exec, 'patch_match_stereo',
            '--workspace_path', dense_dir
        ], check=True)

        subprocess.run([
            colmap_exec, 'stereo_fusion',
            '--workspace_path', dense_dir,
            '--output_path', os.path.join(dense_dir, 'fused.ply')
        ], check=True)

        # Export text format
        subprocess.run([
            colmap_exec, 'model_converter',
            '--input_path', os.path.join(sparse_dir, '0'),
            '--output_path', text_dir,
            '--output_type', 'TXT'
        ], check=True)

        print("COLMAP pipeline completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"COLMAP failed at step: {e.cmd}")
        return False

if __name__ == '__main__':
    success = run_colmap_pipeline()
    sys.exit(0 if success else 1)