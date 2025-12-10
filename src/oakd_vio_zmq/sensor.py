from typing import Any, Callable, Iterable

import depthai as dai

from oakd_vio_zmq._typing import DepthMap, Image, Pointcloud, TransformationMatrix
from oakd_vio_zmq.helpers import create_transformation_matrix


def start_oakd(
    callback: Callable[[Image, Pointcloud, TransformationMatrix], Any] | None = None,
    fps: int = 30,
    width: int = 640,
    height: int = 400,
    # ) -> None:
) -> Iterable[tuple[Image, DepthMap, Pointcloud, TransformationMatrix]]:
    """
    Start the OAK-D pipeline and continuously yield RGB frames, point clouds, and VIO transformations.

    This function initializes an OAK-D pipeline with RGB, stereo, IMU, and visual-inertial odometry (VIO)
    modules. It streams synchronized RGB frames, point clouds, and 4x4 transformation matrices representing
    the estimated camera pose over time. The function is a generator that yields one set of data per frame
    until the pipeline stops.

    Args:
        fps (int): Target frame rate for the camera streams.
        width (int): Width of the RGB and stereo image frames.
        height (int): Height of the RGB and stereo image frames.

    Yields:
        tuple:
            rgb (Image): RGB frame from the OAK-D camera. Shape: `(H, W, 3)`
            depth_map (DepthMap): The depth map of the image. Shape: `(H, W)`
            pointcloud (Pointcloud): Point cloud array from the RGBD node. Shape: `(N, 3)`
            transform (TransformationMatrix): Homogeneous transformation matrix representing camera pose. Shape: `(4, 4)`

    ## Notes
        - `H` = Image height in pixels
        - `W` = Image width in pixels
        - `N` = Number of points in the point cloud. Usually `N = H * W` for dense RGB-D.
        - Transformation matrix is a 4x4 NumPy array representing rotation and translation in homogeneous coordinates.
    """
    with dai.Pipeline() as p:
        # Define sources and outputs
        color = p.create(dai.node.Camera).build(boardSocket=dai.CameraBoardSocket.CAM_A)
        left = p.create(dai.node.Camera).build(
            dai.CameraBoardSocket.CAM_B, sensorFps=fps
        )
        right = p.create(dai.node.Camera).build(
            dai.CameraBoardSocket.CAM_C, sensorFps=fps
        )

        rgbd = p.create(dai.node.RGBD).build()

        imu = p.create(dai.node.IMU)
        stereo = p.create(dai.node.StereoDepth)
        featureTracker = p.create(dai.node.FeatureTracker)
        odom = p.create(dai.node.RTABMapVIO)

        imu.enableIMUSensor(
            [dai.IMUSensor.ACCELEROMETER_RAW, dai.IMUSensor.GYROSCOPE_RAW], 200
        )
        imu.setBatchReportThreshold(1)
        imu.setMaxBatchReports(10)

        featureTracker.setHardwareResources(1, 2)
        featureTracker.initialConfig.setCornerDetector(
            dai.FeatureTrackerConfig.CornerDetector.Type.HARRIS
        )
        featureTracker.initialConfig.setNumTargetFeatures(1000)
        featureTracker.initialConfig.setMotionEstimator(False)
        featureTracker.initialConfig.FeatureMaintainer.minimumDistanceBetweenFeatures = 49

        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.DEFAULT)
        stereo.setExtendedDisparity(False)
        stereo.setLeftRightCheck(True)
        stereo.setRectifyEdgeFillColor(0)
        stereo.enableDistortionCorrection(True)
        stereo.initialConfig.setLeftRightCheckThreshold(10)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_B)

        # Linking
        color_out = color.requestOutput(
            size=(width, height), fps=fps, type=dai.ImgFrame.Type.RGB888i
        )
        left.requestOutput((width, height)).link(stereo.left)
        right.requestOutput((width, height)).link(stereo.right)
        stereo.rectifiedLeft.link(featureTracker.inputImage)
        featureTracker.passthroughInputImage.link(odom.rect)
        stereo.depth.link(odom.depth)
        stereo.depth.link(rgbd.inDepth)
        left.requestOutput((width, height)).link(rgbd.inColor)

        featureTracker.outputFeatures.link(odom.features)
        imu.out.link(odom.imu)

        q_cam = color_out.createOutputQueue()
        q_odom = odom.transform.createOutputQueue()
        q_pcl = rgbd.pcl.createOutputQueue()
        q_depth = stereo.depth.createOutputQueue()

        p.start()

        while p.isRunning():
            rgb = q_cam.get().getCvFrame()  # type: ignore
            transform = q_odom.get()
            pcl = q_pcl.get().getPoints()  # type: ignore
            depth = q_depth.get().getFrame()  # type: ignore

            quaternion, translation = (
                transform.getQuaternion(),  # type: ignore
                transform.getTranslation(),  # type: ignore
            )
            qw, qx, qy, qz = quaternion.qw, quaternion.qx, quaternion.qy, quaternion.qz
            tx, ty, tz = translation.x, translation.y, translation.z
            transform_matrix = create_transformation_matrix(
                qw=qw, qx=qx, qy=qy, qz=qz, tx=tx, ty=ty, tz=tz
            )

            if callback is not None:
                callback(rgb, pcl, transform_matrix)

            yield rgb, depth, pcl, transform_matrix
