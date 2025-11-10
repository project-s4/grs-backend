import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_with_retries(model: Any, prompt: str, retries: int = 3, timeout: float = 20.0, initial_backoff: float = 1.0):
    """Run model.generate_content(prompt) with retries, timeout and exponential backoff.

    This runs the blocking `model.generate_content` in a threadpool executor via
    loop.run_in_executor and wraps it in asyncio.wait_for to enforce a timeout.
    """
    loop = asyncio.get_running_loop()
    attempt = 1
    last_exc = None
    while attempt <= retries:
        try:
            logger.info(f"Attempt {attempt} to call Gemini model: {getattr(model, 'model', getattr(model, 'name', 'unknown'))}")
            fut = loop.run_in_executor(None, lambda: model.generate_content(prompt))
            response = await asyncio.wait_for(fut, timeout=timeout)
            return response
        except asyncio.TimeoutError as te:
            last_exc = te
            logger.warning(f"Gemini call timed out on attempt {attempt}: {te}")
        except Exception as e:
            last_exc = e
            logger.warning(f"Gemini call failed on attempt {attempt}: {e}")

        # backoff before next attempt
        sleep_for = initial_backoff * (2 ** (attempt - 1))
        logger.info(f"Retrying after {sleep_for:.1f}s (attempt {attempt+1}/{retries})")
        try:
            await asyncio.sleep(sleep_for)
        except Exception:
            # ignore cancellation during sleep
            pass
        attempt += 1

    # All retries exhausted, raise the last exception
    logger.error(f"All Gemini attempts failed after {retries} tries. Last error: {last_exc}")
    raise last_exc if last_exc is not None else RuntimeError("Gemini call failed")
