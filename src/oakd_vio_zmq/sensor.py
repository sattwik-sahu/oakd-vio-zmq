from typing import Iterable

import depthai as dai
import numpy as np
from scipy.spatial.transform import Rotation as R

from oakd_vio_zmq._typing import Image, Pointcloud, TransformationMatrix


def start_oakd(
    fps: int = 30, width: int = 640, height: int = 400
) -> Iterable[tuple[Image, Pointcloud, TransformationMatrix]]:
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

        p.start()

        while p.isRunning():
            rgb = q_cam.get().getCvFrame()  # type: ignore
            transform = q_odom.get()
            pcl = q_pcl.get().getPoints()  # type: ignore

            quaternion, translation = (
                transform.getQuaternion(),  # type: ignore
                transform.getTranslation(),  # type: ignore
            )
            qw, qx, qy, qz = quaternion.qw, quaternion.qx, quaternion.qy, quaternion.qz
            tx, ty, tz = translation.x, translation.y, translation.z
            transform_matrix = np.eye(4)
            transform_matrix[:3, :3] = R.from_quat(
                [qw, qx, qy, qz], scalar_first=True
            ).as_matrix()
            transform_matrix[:3, 3] = np.array([tx, ty, tz])

            yield rgb, pcl, transform_matrix
