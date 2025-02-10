import os
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run COLMAP sparse reconstruction pipeline.")
    parser.add_argument('--input', required=True, help="Path to input frames folder")
    parser.add_argument('--output', required=True, help="Path to output COLMAP folder")
    parser.add_argument('--width', type=int, required=True, help="Standardized frame width")
    parser.add_argument('--height', type=int, required=True, help="Standardized frame height")
    args = parser.parse_args()

    # Ensure output directories exist
    database_path = os.path.join(args.output, 'database.db')
    sparse_dir = os.path.join(args.output, 'sparse')
    text_dir = os.path.join(args.output, 'text')
    vocab_tree_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vocab_tree_flickr100K_words32K.bin')

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(sparse_dir, exist_ok=True)
    os.makedirs(text_dir, exist_ok=True)

    # Path to COLMAP.bat
    colmap_executable = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'COLMAP.bat')

    # Step 1: Create COLMAP database
    print("Creating COLMAP database...")
    subprocess.run([colmap_executable, 'database_creator', '--database_path', database_path], check=True)

    # Step 2: Feature extraction
    print("Running feature extraction...")
    subprocess.run([
        colmap_executable, 'feature_extractor',
        '--database_path', database_path,
        '--image_path', args.input,
        '--ImageReader.camera_model', 'SIMPLE_PINHOLE',
        '--ImageReader.camera_params', f"{max(args.width, args.height) * 0.8},{args.width / 2},{args.height / 2}",
        '--SiftExtraction.max_image_size', str(max(args.width, args.height))
    ], check=True)

    # Step 3: Feature matching using vocabulary tree
    print("Running vocabulary tree feature matching...")
    if not os.path.exists(vocab_tree_path):
        raise FileNotFoundError(f"Vocabulary tree file not found: {vocab_tree_path}")
    subprocess.run([
        colmap_executable, 'vocab_tree_matcher',
        '--database_path', database_path,
        '--VocabTreeMatching.vocab_tree_path', vocab_tree_path
    ], check=True)

    # Step 4: Sparse reconstruction
    print("Running sparse reconstruction...")
    subprocess.run([
        colmap_executable, 'mapper',
        '--database_path', database_path,
        '--image_path', args.input,
        '--output_path', sparse_dir
    ], check=True)

    # Step 5: Convert sparse model to TXT format for possible future processing
    print("Converting sparse model to TXT format...")
    subprocess.run([
        colmap_executable, 'model_converter',
        '--input_path', os.path.join(sparse_dir, '0'),
        '--output_path', text_dir,
        '--output_type', 'TXT'
    ], check=True)

    print("Sparse reconstruction completed successfully.")

if __name__ == '__main__':
    main()