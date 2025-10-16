import zmq
import ormsgpack
from oakd_vio_zmq._typing import Image, Pointcloud, TransformationMatrix
from oakd_vio_zmq.helpers import get_zmq_uri
from oakd_vio_zmq.utils import create_metadata
from oakd_vio_zmq.sensor import start_oakd


class Publisher:
    """RGBD VIO message publisher"""

    def __init__(self, stream_name: str, fps: int) -> None:
        self._stream_uri = get_zmq_uri(name=stream_name)
        self._ctx = zmq.Context[zmq.Socket[bytes]]()
        self._socket = self._ctx.socket(zmq.PUB)
        self._fps = fps

    def connect_zmq(self) -> None:
        self._socket.bind(addr=self._stream_uri)

    def _send(
        self, rgb: Image, pointcloud: Pointcloud, transform: TransformationMatrix
    ) -> None:
        # Create metadata
        metadata = create_metadata(rgb=rgb, pointcloud=pointcloud, transform=transform)

        # Send multipart data
        self._socket.send_multipart(
            [
                ormsgpack.packb(metadata),
                *[zmq.Frame(m) for m in (rgb, pointcloud, transform)],
            ]
        )

    def start(self) -> None:
        for rgb, pointcloud, transform in start_oakd(fps=self._fps):
            self._send(rgb=rgb, pointcloud=pointcloud, transform=transform)
