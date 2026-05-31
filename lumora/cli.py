"""LumoraAI CLI - `lumora`."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from lumora.client import LumoraClient
from lumora.config import DEFAULT_TOML_TEMPLATE, load_config_from_toml
from lumora.exceptions import LumoraError


app = typer.Typer(
    help="LumoraAI - Make every model smarter, cheaper, and easier to control.",
    no_args_is_help=True,
)
cache_app = typer.Typer(help="Cache utilities.")
app.add_typer(cache_app, name="cache")

console = Console()

CONFIG_FILENAME = ".lumora.toml"


def _config_path() -> Path:
    return Path.cwd() / CONFIG_FILENAME


def _load_client() -> LumoraClient:
    cfg_path = _config_path()
    if not cfg_path.exists():
        console.print(
            f"[red]No {CONFIG_FILENAME} found in this folder.[/red] "
            "Run [bold]lumora init[/bold] first."
        )
        raise typer.Exit(code=2)
    cfg = load_config_from_toml(cfg_path)
    return LumoraClient(config=cfg)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config."),
) -> None:
    """Create a starter .lumora.toml in the current directory."""
    path = _config_path()
    if path.exists() and not force:
        console.print(f"[yellow]{CONFIG_FILENAME} already exists.[/yellow] Use --force to overwrite.")
        raise typer.Exit(code=1)
    path.write_text(DEFAULT_TOML_TEMPLATE, encoding="utf-8")
    console.print(f"[green]Created[/green] {path}")
    console.print(
        "Set the env var for your provider key, e.g.:\n"
        "  [bold]setx OPENROUTER_API_KEY \"sk-or-...\"[/bold]  (Windows)\n"
        "  [bold]export OPENROUTER_API_KEY=\"sk-or-...\"[/bold]  (macOS/Linux)"
    )


@app.command()
def chat(
    prompt: str = typer.Argument(..., help="Your prompt."),
    quality: str = typer.Option("balanced", "--quality", "-q", help="cheap | balanced | smart"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override model."),
    enhance: bool = typer.Option(False, "--enhance/--no-enhance", help="Enable prompt enhancement."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache for this call."),
) -> None:
    """Send a one-off chat prompt through LumoraAI."""
    client = _load_client()
    try:
        resp = client.chat(
            messages=[{"role": "user", "content": prompt}],
            quality=quality,
            model=model,
            enhance_prompt=enhance,
            use_cache=not no_cache,
        )
    except LumoraError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    console.rule(f"[bold]{resp.provider_used} :: {resp.model_used}[/bold]")
    console.print(resp.content)
    console.rule()
    console.print(
        f"cache_hit={resp.cache_hit}  cost=${resp.estimated_cost:.6f}  "
        f"in≈{resp.estimated_input_tokens}t  out≈{resp.estimated_output_tokens}t  "
        f"latency={resp.latency_ms}ms"
    )


@cache_app.command("stats")
def cache_stats() -> None:
    """Show cache statistics."""
    client = _load_client()
    if client.cache is None:
        console.print("[yellow]Cache is disabled in config.[/yellow]")
        raise typer.Exit()
    stats = client.cache.stats()
    table = Table(title="LumoraAI Cache Stats")
    table.add_column("Key")
    table.add_column("Value")
    for k, v in stats.items():
        table.add_row(str(k), str(v))
    console.print(table)


@cache_app.command("clear")
def cache_clear() -> None:
    """Delete all cached responses."""
    client = _load_client()
    if client.cache is None:
        console.print("[yellow]Cache is disabled in config.[/yellow]")
        raise typer.Exit()
    n = client.cache.clear()
    console.print(f"[green]Cleared {n} cached entries.[/green]")


@app.command()
def usage() -> None:
    """Print usage and savings summary for this session.

    Note: usage is tracked in-process. Running `lumora usage` in a fresh
    terminal will show an empty session. Use savings_report() in code for
    long-lived processes, or look forward to the SaaS dashboard.
    """
    client = _load_client()
    summary = client.usage_summary()
    report = client.savings_report()

    t = Table(title="LumoraAI Usage Summary (this process)")
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_row("Total requests", str(summary.total_requests))
    t.add_row("Cache hits", str(summary.cache_hits))
    t.add_row("Input tokens", str(summary.total_input_tokens))
    t.add_row("Output tokens", str(summary.total_output_tokens))
    t.add_row("Total spend (USD)", f"${summary.total_cost:.6f}")
    console.print(t)

    s = Table(title="LumoraAI Savings Report")
    s.add_column("Metric")
    s.add_column("Value", justify="right")
    s.add_row("Routed to cheap", str(report.routed_to_cheap))
    s.add_row("Routed to local", str(report.routed_to_local))
    s.add_row("Saved from cache (USD)", f"${report.saved_from_cache_usd:.6f}")
    s.add_row("Saved from routing (USD)", f"${report.saved_from_routing_usd:.6f}")
    s.add_row("Total savings (USD)", f"${report.total_savings_usd:.6f}")
    s.add_row("Savings %", f"{report.savings_pct}%")
    console.print(s)


if __name__ == "__main__":  # pragma: no cover
    app()
