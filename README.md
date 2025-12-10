# OAKD VIO ZeroMQ

Use the OAK-D RGBD camera for robotics.

## Installation

> [!NOTE]
> 1. Installing `oakd_vio_zmq` requires **Python 3.10** and above.
> 2. `depthai` must be installed using the instructions [here](https://github.com/luxonis/depthai-core/tree/develop) as the RTABMap VIO feature is in _early access preview_.

### Installation with `pip`

```bash
pip install git+https://github.com/sattwik-sahu/oakd-vio-zmq.git
pip install --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ --pre -U depthai
```
### Installation with `uv`

```bash
uv add git+https://github.com/sattwik-sahu/oakd-vio-zmq.git
uv pip install --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ --pre -U depthai
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
    uv pip install --editable .

    uv pip install --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ --pre -U depthai
    ```

## Usage

1. Start the sensor publisher
    ```bash
    oakd-vio-zmq <STREAM_NAME> --fps <FPS>
    ```
2. Get the data in Python
    ```python
    import cv2
    from oakd_vio_zmq.subscribe import Subscriber


    def main():
        sub = Subscriber(stream_name="oakd")
        sub.connect()
        while True:
            msg = sub.get_next()

            if msg is not None:
                # Extract required sensor readings
                rgb = msg.rgb
                depth = msg.depth
                pointcloud = msg.pointcloud
                T = msg.transform

                # Show RGB image and depth map
                cv2.imshow("Camera", msg.rgb)
                cv2.imshow("Depth", msg.depth / 10e3)
                cv2.waitKey(1)

                # Show other shapes
                print(f"RGB image shape: {rgb.shape}")
                print(f"Depth map shape: {depth.shape}")
                print(f"Pointcloud shape: {pointcloud.shape}")
                print(f"Transformation matrix:\n{T}")


    if __name__ == "__main__":
        main()
    ```

> [!WARNING]
> Known issues include the VIO output getting stuck at the identity matrix. This is possibly an issue with the [`RTABMapVIO` node in `depthai`](https://docs.luxonis.com/software-v3/depthai/examples/rvc2/vslam/rtab_map_vio/).
