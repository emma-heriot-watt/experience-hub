import typer

from emma_experience_hub.commands.simbot.cli import app as simbot_cli


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Commands you might need to setup your environment for EMMA, and run EMMA.",
)


app.add_typer(simbot_cli, name="simbot")


if __name__ == "__main__":
    app()
