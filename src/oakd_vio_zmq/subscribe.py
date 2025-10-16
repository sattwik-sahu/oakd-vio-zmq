import zmq
from oakd_vio_zmq._typing import RGBD_VIO_Message
from typing import Optional, Union
from oakd_vio_zmq.helpers import get_zmq_uri
from oakd_vio_zmq.utils import parse_message


class Subscriber:
    """Subscriber for RGBD VIO messages"""

    def __init__(self, stream_name: str) -> None:
        self._stream_uri = get_zmq_uri(stream_name)
        self._ctx = zmq.Context[zmq.Socket[bytes]]()
        self._socket = self._ctx.socket(zmq.SUB)

    def connect(self) -> None:
        self._socket.connect(addr=self._stream_uri)
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self._socket.setsockopt(zmq.RCVHWM, 1)
        self._socket.setsockopt(zmq.LINGER, 0)

    def _get_latest_frame(self) -> Optional[tuple[Union[bytes, zmq.Frame], ...]]:
        latest = None
        while True:
            try:
                latest = self._socket.recv_multipart(flags=zmq.NOBLOCK)
            except zmq.Again:
                break
        return latest  # type: ignore

    def get_next(self) -> Optional[RGBD_VIO_Message]:
        msg = self._get_latest_frame()
        if msg is not None:
            metadata_bytes, rgb_frame, pointcloud_frame, transform_frame = msg
            message = parse_message(
                metadata_bytes=metadata_bytes,  # type: ignore
                rgb_frame=rgb_frame,  # type: ignore
                pointcloud_frame=pointcloud_frame,  # type: ignore
                transform_frame=transform_frame,  # type: ignore
            )
            return message
