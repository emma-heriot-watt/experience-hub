import typer

from emma_experience_hub.commands.docker import app as docker_cli


app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(docker_cli, name="docker")

if __name__ == "__main__":
    app()
