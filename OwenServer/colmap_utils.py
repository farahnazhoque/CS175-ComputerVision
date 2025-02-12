import numpy as np
import struct
import os
from collections import namedtuple

CameraModel = namedtuple("CameraModel", ["model_id", "model_name", "num_params"])
Camera = namedtuple("Camera", ["id", "model", "width", "height", "params"])
BaseImage = namedtuple("Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])

def read_next_bytes(fid, num_bytes, format_char_sequence, endian_character="<"):
    data = fid.read(num_bytes)
    return struct.unpack(endian_character + format_char_sequence, data)

def read_cameras_binary(path_to_model_file):
    cameras = {}
    with open(path_to_model_file, "rb") as fid:
        num_cameras = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_cameras):
            camera_properties = read_next_bytes(fid, 24, "iiQQ")
            camera_id = camera_properties[0]
            model_id = camera_properties[1]
            model_name = CAMERA_MODELS[model_id].model_name
            width = camera_properties[2]
            height = camera_properties[3]
            num_params = CAMERA_MODELS[model_id].num_params
            params = list(read_next_bytes(fid, 8*num_params, "d"*num_params))
            cameras[camera_id] = Camera(id=camera_id, model=model_name,
                                      width=width, height=height,
                                      params=np.array(params))
    return cameras

def read_images_binary(path_to_model_file):
    images = {}
    with open(path_to_model_file, "rb") as fid:
        num_reg_images = read_next_bytes(fid, 8, "Q")[0]
        for _ in range(num_reg_images):
            image_id = read_next_bytes(fid, 4, "I")[0]
            qvec = np.array(read_next_bytes(fid, 32, "dddd"))
            tvec = np.array(read_next_bytes(fid, 24, "ddd"))
            camera_id = read_next_bytes(fid, 4, "I")[0]
            image_name = ""
            current_char = read_next_bytes(fid, 1, "c")[0]
            while current_char != b"\x00":
                image_name += current_char.decode("utf-8")
                current_char = read_next_bytes(fid, 1, "c")[0]
            num_points2D = read_next_bytes(fid, 8, "Q")[0]
            x_y_id = list(read_next_bytes(fid, 24*num_points2D, "ddq"*num_points2D))
            xys = np.array(x_y_id[::3]).reshape(-1, 2)
            point3D_ids = np.array(x_y_id[2::3])
            images[image_id] = BaseImage(id=image_id, qvec=qvec, tvec=tvec,
                                       camera_id=camera_id, name=image_name,
                                       xys=xys, point3D_ids=point3D_ids)
    return images

# Supported camera models (add more if needed)
CAMERA_MODELS = {
    CameraModel(0, "SIMPLE_PINHOLE", 3),
    CameraModel(1, "PINHOLE", 4),
    CameraModel(2, "SIMPLE_RADIAL", 4),
    CameraModel(3, "RADIAL", 5),
    CameraModel(4, "OPENCV", 8),
    CameraModel(5, "OPENCV_FISHEYE", 8),
    CameraModel(6, "FULL_OPENCV", 12),
}
CAMERA_MODELS = dict([(c.model_id, c) for c in CAMERA_MODELS])