import typer

from emma_experience_hub.commands.build_emma import build_emma
from emma_experience_hub.commands.teach import app as teach_cli
from emma_experience_hub.common import load_env_vars


load_env_vars()

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Commands you might need to setup your environment for EMMA, and run EMMA.",
)


app.command()(build_emma)

app.add_typer(teach_cli, name="teach")

if __name__ == "__main__":
    app()
