# OAKD VIO ZeroMQ

Use the OAK-D RGBD camera for robotics.

## Installation

### Installation with `pip`

```bash
pip install git+https://github.com/sattwik-sahu/oakd-vio-zmq.git
```
### Installation with `uv`

```bash
uv add git+https://github.com/sattwik-sahu/oakd-vio-zmq.git
```

### Install from Source

1. Clone the repo
    ```bash
    git clone https://github.com/sattwik-sahu/oakd-vio-zmq.git oakd_vio_zmq
    ```
2. Install as an editable package
    ```bash
    cd oakd_vio_zmq
    pip install -e "."
    # Or with uv
    uv install --editable .
    ```

## Usage

1. Start the sensor publisher
    ```bash
    oakd-vio-zmq <STREAM_NAME> --fps <FPS>
    ```
2. Get the data in Python
    ```python
    from oakd_vio_zmq.subscribe import Subscriber
    import cv2


    def main():
        sub = Subscriber(stream_name="oakd")
        sub.connect()
        while True:
            msg = sub.get_next()
            if msg is not None:
                cv2.imshow("Camera", msg.rgb)  # Shape: (640, 400, 3)
                cv2.waitKey(1)
                print(f"Pointcloud shape: {msg.pointcloud.shape}") # Shape: (256000, 3)
                print(f"Transformation matrix:\n{msg.transform}") # Shape: (4, 4)


    if __name__ == "__main__":
        main()
    ```
