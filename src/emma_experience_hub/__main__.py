import rich_click as click
from rich_click import typer

from emma_experience_hub.commands.docker import app as docker_cli


click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = False

app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(docker_cli, name="docker")

if __name__ == "__main__":
    app()
