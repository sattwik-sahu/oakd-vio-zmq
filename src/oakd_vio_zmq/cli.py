import typer
from oakd_vio_zmq.publish import Publisher
from typing import Annotated
from rich.console import Console

app = typer.Typer(help="RTABMAP VIO with the OAK-D camera")


@app.command(name="run")
def run(
    stream_name: Annotated[
        str, typer.Argument(help="The stream name of sensor publisher")
    ],
    fps: Annotated[int, typer.Option(help="The camera FPS")] = 30,
):
    console = Console()

    with console.status("Creating publisher"):
        pub = Publisher(stream_name=stream_name, fps=fps)
    console.print(f"Created publisher for stream [bold cyan]{stream_name}[/]")

    with console.status("Binding to stream"):
        try:
            pub.connect_zmq()
        except Exception as ex:
            console.print("[red]Could not connect to stream[/]")
            raise ex
    console.print(f"[green]Connected successfully to {pub._stream_uri}[/]")

    try:
        console.print("[cyan]:rocket: Started publisher[/]")
        pub.start()
    except Exception as ex:
        console.print("[red]Error encountered in publisher[/]")
        raise ex
