import shutil
import typer
import subprocess
from pathlib import Path
import importlib.resources as resources
import gltest

app = typer.Typer(invoke_without_command=True)


@app.callback()
def test(ctx: typer.Context):
    """
    Default command: Run tests using pytest.
    """
    if ctx.invoked_subcommand is None:
        command = ["pytest"]
        typer.echo(f"Running command: {' '.join(command)}")
        result = subprocess.run(command)
        raise typer.Exit(code=result.returncode)


@app.command()
def init(
    output_dir: Path = typer.Option(
        ".", "--output", "-o", help="Directory where the project will be created"
    ),
):
    """
    Create a new testing project by copying the sample project structure,
    excluding __pycache__ and .pyc files. Prevents overwriting if output exists.
    """
    output_dir = Path(output_dir)

    # Check if output directory exists and is not empty
    if output_dir.exists() and any(output_dir.iterdir()):
        typer.echo(
            f"❌ Error: Output directory '{output_dir}' already exists and is not empty.",
            err=True,
        )
        raise typer.Exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Locate the sample project directory inside the package
        sample_dir = resources.files(gltest).joinpath("sample_project")

        def ignore_pycache_and_pyc(dir, contents):
            ignored = []
            for name in contents:
                if name == "__pycache__" or name.endswith(".pyc"):
                    ignored.append(name)
            return ignored

        for item in sample_dir.iterdir():
            dest = output_dir / item.name
            if item.is_dir():
                shutil.copytree(
                    item, dest, dirs_exist_ok=True, ignore=ignore_pycache_and_pyc
                )
            elif not item.name.endswith(".pyc"):
                shutil.copy2(item, dest)

        typer.echo(f"✅ Successfully created project in {output_dir} directory")
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(1)


def main():
    app()
