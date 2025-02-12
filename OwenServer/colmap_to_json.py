import os
import json
import numpy as np
from colmap_utils import read_cameras_binary, read_images_binary

def qvec2rotmat(qvec):
    return np.array([
        [1 - 2 * qvec[2]**2 - 2 * qvec[3]**2,
         2 * qvec[1] * qvec[2] - 2 * qvec[0] * qvec[3],
         2 * qvec[1] * qvec[3] + 2 * qvec[0] * qvec[2]],
        [2 * qvec[1] * qvec[2] + 2 * qvec[0] * qvec[3],
         1 - 2 * qvec[1]**2 - 2 * qvec[3]**2,
         2 * qvec[2] * qvec[3] - 2 * qvec[0] * qvec[1]],
        [2 * qvec[1] * qvec[3] - 2 * qvec[0] * qvec[2],
         2 * qvec[2] * qvec[3] + 2 * qvec[0] * qvec[1],
         1 - 2 * qvec[1]**2 - 2 * qvec[2]**2]
        ])

def convert_colmap(colmap_dir, output_json, image_folder="images"):
    cameras = read_cameras_binary(os.path.join(colmap_dir, 'sparse/0/cameras.bin'))
    images = read_images_binary(os.path.join(colmap_dir, 'sparse/0/images.bin'))

    meta = {"camera_angle_x": 0, "frames": []}
    
    # Find reference camera
    cam = cameras[1]
    meta["camera_angle_x"] = 2 * np.arctan(cam.params[0] / (2 * cam.params[1]))

    # Sort images by name (assumes sequential numbering)
    sorted_images = sorted(images.values(), key=lambda x: x.name)
    total_frames = len(sorted_images)
    
    for idx, img in enumerate(sorted_images):
        # COLMAP to NeRF coordinate system conversion
        rot = qvec2rotmat(img.qvec)
        trans = img.tvec.reshape(3, 1)
        w2c = np.concatenate([rot, trans], 1)
        w2c = np.concatenate([w2c, [[0, 0, 0, 1]]], 0)
        c2w = np.linalg.inv(w2c)

        frame = {
            "file_path": os.path.join(image_folder, img.name),
            "time": idx / (total_frames - 1),
            "transform_matrix": c2w.tolist()
        }
        meta["frames"].append(frame)

    with open(output_json, 'w') as f:
        json.dump(meta, f, indent=2)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--colmap_dir", required=True)
    parser.add_argument("--output_json", required=True)
    args = parser.parse_args()
    convert_colmap(args.colmap_dir, args.output_json)