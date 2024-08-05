import pyrealsense2 as rs
import numpy as np
import cv2


def convert_coordinates(x2, y2, z2):
    xx = True

    if xx:
        theta1 = 0
        theta2 = 0
        thetax = 345
        x0 = 600 / 1000 # 280
        y0 = -350 /1000 # 200
        z0 = -400
    else:

        theta1 = 0
        theta2 = 0
        thetax = 0
        x0 = 0  # 280 #
        y0 = 0  # 200 #
        z0 = 0
    # Convert degrees to radians
    theta1_rad = np.radians(theta1)
    theta2_rad = np.radians(theta2)

    thetax_rad = np.radians(thetax)

    # Rotation matrix transposed for theta2 (Y-axis rotation), since we're applying the inverse
    Ry2T = np.array([
        [np.cos(theta2_rad), 0, -np.sin(theta2_rad)],
        [0, 1, 0],
        [np.sin(theta2_rad), 0, np.cos(theta2_rad)]
    ])

    # Rotation matrix transposed for theta1 (Z-axis rotation), since we're applying the inverse
    Rz1T = np.array([
        [np.cos(theta1_rad), np.sin(theta1_rad), 0],
        [-np.sin(theta1_rad), np.cos(theta1_rad), 0],
        [0, 0, 1]
    ])
    Rx1T = np.array([
        [1, 0, 0],
        [0, np.cos(thetax_rad), -np.sin(thetax_rad)],
        [0, np.sin(thetax_rad), np.cos(thetax_rad)],

    ])

    # Original point in system 2
    P2 = np.array([x2, y2, z2])

    # Apply the rotations (Note: np.dot() for 2D can be replaced by @ for matrix multiplication)
    # First apply Rz1T, then Ry2T
    # P_rotated = np.dot(Rz1T, np.dot(Ry2T, P2))
    P_rotated = np.dot(Rx1T, P2)
    # Apply translation
    p2 = P_rotated + np.array([x0, y0, z0])
    return p2[0], -p2[1], p2[2]


class Camera:
    def __init__(self):
        # Configure depth and colors cameras
        self.pipeline = rs.pipeline()

        config = rs.config()
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        self.color_frame = None
        self.depth_frame = None

        # Start streaming
        profile = self.pipeline.start(config)

        # Combining cameras
        align_to = rs.stream.color
        self.align = rs.align(align_to)

        self.depth_intrinsic = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

    def get_frame_stream(self):
        frames = self.pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        self.color_frame = color_frame
        self.depth_frame = depth_frame

        if not depth_frame or not color_frame:
            print("There is no access. Maybe another camera")
            return None, None

        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        return color_image, depth_colormap

    def get_distance_and_coordinate_point(self, x, y):
        distance = self.depth_frame.get_distance(x, y)
        x, y, z = rs.rs2_deproject_pixel_to_point(self.depth_intrinsic, [x, y], distance)
        distance_mm = round(distance * 1000)
        x, y, z = convert_coordinates(x, y, z)
        x_mm, y_mm, z_mm = round(x * 1000), round(y * 1000), round(z * 1000)
        return distance_mm, (x_mm, y_mm, z_mm)

    def release(self):
        self.pipeline.stop()

