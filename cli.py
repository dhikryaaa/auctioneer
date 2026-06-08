#!/usr/bin/env python3
"""Auctioneer CLI — interact with the auction platform via the API gateway."""
import json
import os
from pathlib import Path
from typing import Optional

import httpx
import typer

# ── App & subcommands ─────────────────────────────────────────────────────────
app        = typer.Typer(help="Auctioneer CLI")
auth_app   = typer.Typer(help="Authentication")
auction_app = typer.Typer(help="Auction management")
bids_app   = typer.Typer(help="Bidding")
activity_app = typer.Typer(help="Activity & history")

app.add_typer(auth_app,     name="auth")
app.add_typer(auction_app,  name="auctions")
app.add_typer(bids_app,     name="bids")
app.add_typer(activity_app, name="activity")

# ── Config ────────────────────────────────────────────────────────────────────
GATEWAY_URL  = os.getenv("GATEWAY_URL", "http://localhost:8000")
_DIR         = Path.home() / ".auctioneer"
_TOKEN_FILE  = _DIR / "token"
_COOKIE_FILE = _DIR / "cookies"

# ── Credential helpers ────────────────────────────────────────────────────────
def _save_token(token: str):
    _DIR.mkdir(parents=True, exist_ok=True)
    _TOKEN_FILE.write_text(token)

def _load_token() -> str | None:
    return _TOKEN_FILE.read_text().strip() if _TOKEN_FILE.exists() else None

def _load_cookies() -> dict:
    return json.loads(_COOKIE_FILE.read_text()) if _COOKIE_FILE.exists() else {}

def _save_cookies(res: httpx.Response):
    if "refresh_token" in res.cookies:
        _DIR.mkdir(parents=True, exist_ok=True)
        cookies = _load_cookies()
        cookies["refresh_token"] = res.cookies["refresh_token"]
        _COOKIE_FILE.write_text(json.dumps(cookies))

def _auth_headers() -> dict:
    token = _load_token()
    if not token:
        typer.echo("Not logged in. Run: python cli.py auth login", err=True)
        raise typer.Exit(1)
    return {"Authorization": f"Bearer {token}"}

# ── Output helpers ────────────────────────────────────────────────────────────
def _print(data):
    typer.echo(json.dumps(data, indent=2, default=str))

def _handle(res: httpx.Response):
    try:
        data = res.json()
    except Exception:
        data = res.text
    if res.is_error:
        typer.echo(f"[{res.status_code}] {json.dumps(data, indent=2, default=str)}", err=True)
        raise typer.Exit(1)
    _print(data)


# ── AUTH ──────────────────────────────────────────────────────────────────────
@auth_app.command("register")
def auth_register(
    name:     str = typer.Option(..., prompt=True),
    email:    str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Register a new account."""
    res = httpx.post(
        f"{GATEWAY_URL}/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    if not res.is_error:
        _save_token(res.json()["access_token"])
        _save_cookies(res)
        typer.echo("Registered and logged in.")
    _handle(res)


@auth_app.command("login")
def auth_login(
    email:    str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Login and save the access token locally."""
    res = httpx.post(
        f"{GATEWAY_URL}/auth/login",
        json={"email": email, "password": password},
    )
    if not res.is_error:
        _save_token(res.json()["access_token"])
        _save_cookies(res)
        typer.echo("Logged in.")
    _handle(res)


@auth_app.command("refresh")
def auth_refresh():
    """Refresh the access token using the saved refresh cookie."""
    res = httpx.post(f"{GATEWAY_URL}/auth/refresh", cookies=_load_cookies())
    if not res.is_error:
        _save_token(res.json()["access_token"])
        _save_cookies(res)
        typer.echo("Token refreshed.")
    _handle(res)


@auth_app.command("logout")
def auth_logout():
    """Logout and clear saved credentials."""
    res = httpx.post(
        f"{GATEWAY_URL}/auth/logout",
        headers=_auth_headers(),
        cookies=_load_cookies(),
    )
    _TOKEN_FILE.unlink(missing_ok=True)
    _COOKIE_FILE.unlink(missing_ok=True)
    _handle(res)


@auth_app.command("me")
def auth_me():
    """Get current user profile."""
    res = httpx.get(f"{GATEWAY_URL}/auth/me", headers=_auth_headers())
    _handle(res)


@auth_app.command("users")
def auth_users():
    """[Admin] List all users."""
    res = httpx.get(f"{GATEWAY_URL}/auth/admin/users", headers=_auth_headers())
    _handle(res)


@auth_app.command("user-status")
def auth_user_status(user_id: int = typer.Argument(..., help="User ID")):
    """[Admin] Get a user's status."""
    res = httpx.get(f"{GATEWAY_URL}/auth/admin/user_status/{user_id}", headers=_auth_headers())
    _handle(res)


# ── AUCTIONS ──────────────────────────────────────────────────────────────────
@auction_app.command("list")
def auctions_list():
    """List all active auctions (public)."""
    res = httpx.get(f"{GATEWAY_URL}/auctions/")
    _handle(res)


@auction_app.command("list-all")
def auctions_list_all():
    """[Admin] List all auctions including closed ones."""
    res = httpx.get(f"{GATEWAY_URL}/auctions/all", headers=_auth_headers())
    _handle(res)


@auction_app.command("get")
def auctions_get(auction_id: int = typer.Argument(..., help="Auction ID")):
    """Get a single auction by ID (public)."""
    res = httpx.get(f"{GATEWAY_URL}/auctions/{auction_id}")
    _handle(res)


@auction_app.command("create")
def auctions_create(
    title:          str           = typer.Option(..., prompt=True),
    starting_price: int           = typer.Option(..., prompt=True),
    ends_at:        str           = typer.Option(..., prompt=True, help="ISO format e.g. 2026-12-31T23:59:59"),
    description:    Optional[str] = typer.Option(None, help="Optional description"),
):
    """Create a new auction."""
    res = httpx.post(
        f"{GATEWAY_URL}/auctions/",
        json={
            "title": title,
            "starting_price": starting_price,
            "ends_at": ends_at,
            "description": description,
        },
        headers=_auth_headers(),
    )
    _handle(res)


@auction_app.command("edit")
def auctions_edit(
    auction_id:     int           = typer.Argument(..., help="Auction ID"),
    title:          Optional[str] = typer.Option(None),
    description:    Optional[str] = typer.Option(None),
    starting_price: Optional[int] = typer.Option(None),
    ends_at:        Optional[str] = typer.Option(None, help="ISO format"),
):
    """Edit an auction (owner only, only if no bids)."""
    payload = {k: v for k, v in {
        "title": title,
        "description": description,
        "starting_price": starting_price,
        "ends_at": ends_at,
    }.items() if v is not None}
    res = httpx.patch(f"{GATEWAY_URL}/auctions/{auction_id}", json=payload, headers=_auth_headers())
    _handle(res)


@auction_app.command("delete")
def auctions_delete(auction_id: int = typer.Argument(..., help="Auction ID")):
    """Delete an auction (owner only, only if no bids)."""
    res = httpx.delete(f"{GATEWAY_URL}/auctions/{auction_id}", headers=_auth_headers())
    _handle(res)


@auction_app.command("close")
def auctions_close(auction_id: int = typer.Argument(..., help="Auction ID")):
    """[Admin] Force close an auction."""
    res = httpx.patch(f"{GATEWAY_URL}/auctions/{auction_id}/close", headers=_auth_headers())
    _handle(res)


@auction_app.command("delete-admin")
def auctions_delete_admin(auction_id: int = typer.Argument(..., help="Auction ID")):
    """[Admin] Force delete an auction."""
    res = httpx.delete(f"{GATEWAY_URL}/auctions/{auction_id}/admin", headers=_auth_headers())
    _handle(res)


# ── BIDS ──────────────────────────────────────────────────────────────────────
@bids_app.command("place")
def bids_place(
    auction_id: int = typer.Option(..., prompt=True, help="Auction ID"),
    amount:     int = typer.Option(..., prompt=True, help="Bid amount"),
):
    """Place a bid on an auction."""
    res = httpx.post(
        f"{GATEWAY_URL}/bids/",
        json={"auction_id": auction_id, "amount": amount},
        headers=_auth_headers(),
    )
    _handle(res)


@bids_app.command("me")
def bids_me():
    """Get my bid history."""
    res = httpx.get(f"{GATEWAY_URL}/bids/me", headers=_auth_headers())
    _handle(res)


@bids_app.command("list")
def bids_list(auction_id: int = typer.Argument(..., help="Auction ID")):
    """List all bids on an auction (public)."""
    res = httpx.get(f"{GATEWAY_URL}/bids/{auction_id}")
    _handle(res)


@bids_app.command("list-all")
def bids_list_all():
    """[Admin] List every bid in the system."""
    res = httpx.get(f"{GATEWAY_URL}/bids/", headers=_auth_headers())
    _handle(res)


# ── ACTIVITY ──────────────────────────────────────────────────────────────────
@activity_app.command("me")
def activity_me():
    """Get my full activity summary (listings + bids)."""
    res = httpx.get(f"{GATEWAY_URL}/activity/me", headers=_auth_headers())
    _handle(res)


@activity_app.command("my-listings")
def activity_my_listings():
    """Get my auction listings."""
    res = httpx.get(f"{GATEWAY_URL}/activity/me/listings", headers=_auth_headers())
    _handle(res)


@activity_app.command("my-bids")
def activity_my_bids():
    """Get my bid activity."""
    res = httpx.get(f"{GATEWAY_URL}/activity/me/bids", headers=_auth_headers())
    _handle(res)


@activity_app.command("user")
def activity_user(user_id: int = typer.Argument(..., help="User ID")):
    """[Admin] Get activity for a specific user."""
    res = httpx.get(f"{GATEWAY_URL}/activity/{user_id}", headers=_auth_headers())
    _handle(res)


if __name__ == "__main__":
    app()
