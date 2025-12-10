import ormsgpack
import zmq

from oakd_vio_zmq._typing import DepthMap, Image, Pointcloud, TransformationMatrix
from oakd_vio_zmq.helpers import get_zmq_uri
from oakd_vio_zmq.sensor import start_oakd
from oakd_vio_zmq.utils import create_metadata


class Publisher:
    """
    Publishes RGB-D and VIO (Visual-Inertial Odometry) data streams over ZeroMQ.

    This class initializes a ZeroMQ PUB socket and continuously transmits RGB images,
    point clouds, and transformation matrices captured from an OAK-D camera at a
    specified frame rate. Each published message contains serialized metadata and
    binary data frames packed efficiently for real-time transmission.
    """

    def __init__(self, stream_name: str, fps: int) -> None:
        """
        Initializes the Publisher with a named stream and target frame rate.

        Args:
            stream_name (str): The name of the ZeroMQ stream. Used to determine the URI for binding.
            fps (int): Target frames per second for the publishing loop.
        """
        self._stream_uri = get_zmq_uri(name=stream_name)
        self._ctx = zmq.Context[zmq.Socket[bytes]]()
        self._socket = self._ctx.socket(zmq.PUB)
        self._fps = fps

    def connect_zmq(self) -> None:
        """
        Binds the ZeroMQ PUB socket to the precomputed stream URI.

        This must be called before starting to publish data. It initializes the
        network endpoint so that subscribers can connect and receive messages.
        """
        self._socket.bind(addr=self._stream_uri)

    def _send(
        self,
        rgb: Image,
        depth: DepthMap,
        pointcloud: Pointcloud,
        transform: TransformationMatrix,
    ) -> None:
        """
        Serializes and transmits a single RGB-D-VIO message via ZeroMQ.

        Args:
            rgb (Image): RGB image frame from the OAK-D camera. Shape: `(H, W, 3)`
            depth (DepthMap): The depth map. Shape: `(H, W)`
            pointcloud (Pointcloud): Corresponding 3D point cloud data. Shape: `(N, 3)`
            transform (TransformationMatrix): Transformation matrix representing camera pose. Shape: `(4, 4)`

        ## Note
            - `H` = Image height in pixels
            - `W` = Image width in pixels
            - `N` = Number of points in pointcloud. `N = H * W` for OAK-D.
        """
        metadata = create_metadata(
            rgb=rgb, depth=depth, pointcloud=pointcloud, transform=transform
        )
        self._socket.send_multipart(
            [
                ormsgpack.packb(metadata),
                *[zmq.Frame(m) for m in (rgb, depth, pointcloud, transform)],
            ]
        )

    def start(self) -> None:
        """
        Begins the continuous publishing loop from the OAK-D sensor.

        This method starts the data stream by iterating over frames from
        the OAK-D camera. Each frame is sent over ZeroMQ as a multipart
        message containing metadata, image, point cloud, and transformation
        data. The loop runs indefinitely at the configured frame rate.
        """
        for rgb, depth, pointcloud, transform in start_oakd(fps=self._fps):
            self._send(rgb=rgb, depth=depth, pointcloud=pointcloud, transform=transform)
