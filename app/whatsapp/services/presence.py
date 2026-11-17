"""WhatsApp typing indicator (also marks the inbound message as read)."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)

_TYPING_REFRESH_SECONDS = 20.0


def inbound_message_id(message: Any) -> str:
    return str(getattr(message, "id", "") or "").strip()


async def indicate_typing(*, client: Any, message: Any) -> bool:
    """Show typing and mark the user's message read (blue ticks)."""

    message_id = inbound_message_id(message)
    if not message_id or client is None:
        return False
    try:
        await client.indicate_typing(message_id=message_id)
        return True
    except Exception:
        logger.warning("whatsapp_indicate_typing_failed", extra={"message_id": message_id})
        return False


@asynccontextmanager
async def typing_while_working(*, client: Any, message: Any) -> AsyncIterator[None]:
    """Keep the typing bubble up until we reply (or ~25s idle)."""

    message_id = inbound_message_id(message)
    if not message_id or client is None:
        yield
        return
    stop = asyncio.Event()

    async def _refresh() -> None:
        while not stop.is_set():
            await indicate_typing(client=client, message=message)
            try:
                await asyncio.wait_for(stop.wait(), timeout=_TYPING_REFRESH_SECONDS)
            except TimeoutError:
                continue

    task = asyncio.create_task(_refresh())
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
