"""Command-line entry point: ``python -m go_arena ...``."""

from __future__ import annotations

import click

from go_arena.agents import list_agents, make_agent
from go_arena.engine.render import render_ascii
from go_arena.engine.types import Color, Pass
from go_arena.tournament.match import play_match


@click.group()
def cli() -> None:
    """go-arena: a 5x5 Go arena with multiple agents."""


@cli.command("agents")
def cmd_agents() -> None:
    """List registered agents."""
    for name in list_agents():
        click.echo(name)


@cli.command("play")
@click.option("--black", "black_name", default="random", help="Black agent name.")
@click.option("--white", "white_name", default="random", help="White agent name.")
@click.option("--time", "time_limit", default=2.0, type=float, help="Per-move time limit (s).")
@click.option("--size", default=5, type=int, help="Board edge length.")
@click.option("--komi", default=2.5, type=float, help="White komi.")
@click.option("--max-moves", default=100, type=int, help="Hard cap on moves.")
@click.option("--verbose", is_flag=True, help="Print the board after each move.")
def cmd_play(
    black_name: str,
    white_name: str,
    time_limit: float,
    size: int,
    komi: float,
    max_moves: int,
    verbose: bool,
) -> None:
    """Play a single match between two agents and print the result."""
    black = make_agent(black_name)
    white = make_agent(white_name)

    def _print_move(board, color, move) -> None:  # type: ignore[no-untyped-def]
        glyph = "X" if color is Color.BLACK else "O"
        if isinstance(move, Pass):
            click.echo(f"\n{glyph} pass")
        else:
            click.echo(f"\n{glyph} -> ({move.row}, {move.col})")
        click.echo(render_ascii(board))

    result = play_match(
        black,
        white,
        board_size=size,
        time_limit=time_limit,
        max_moves=max_moves,
        komi=komi,
        on_move=_print_move if verbose else None,
    )

    click.echo("")
    click.echo("=" * 40)
    if result.forfeit is not None:
        loser, reason = result.forfeit
        click.echo(f"Forfeit: {loser.name} ({reason})")
    click.echo(f"Score: black={result.score['black']:.1f}  white={result.score['white']:.1f}")
    if result.winner is Color.EMPTY:
        click.echo("Result: tie")
    else:
        click.echo(f"Winner: {result.winner.name}")
    click.echo(
        f"Time: black={result.time_used[Color.BLACK]:.2f}s  "
        f"white={result.time_used[Color.WHITE]:.2f}s  "
        f"moves={len(result.moves)}"
    )


if __name__ == "__main__":
    cli()
