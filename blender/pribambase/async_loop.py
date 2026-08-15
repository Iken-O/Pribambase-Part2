# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# Adapted from Blender Cloud Addon (Sybren A. Stüvel, Francesco Siddi, Inês Almeida,
# Antony Riakiotakis) - http://github.com/dfelinto/blender-cloud-addon

"""Manages the asyncio loop"""

import asyncio
import traceback
import concurrent.futures
import logging
import gc

import bpy
from bpy.app.handlers import persistent

log = logging.getLogger(__name__)

# Keep websocket handling responsive without busy-spinning Blender's UI thread.
ASYNC_LOOP_INTERVAL = 0.01

# Tracks whether Blender's asyncio timer can stop after its next iteration.
_stop_after_this_kick = False


def get_event_loop():
    """Return the current loop, creating one when Python has not set one.

    Python 3.14 no longer creates a loop implicitly in
    ``asyncio.get_event_loop()``. Blender drives asyncio manually from a timer,
    so the add-on needs to own and install that loop explicitly.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


def setup_asyncio_executor():
    """Sets up AsyncIO to run properly on each platform"""

    import sys

    loop = get_event_loop()

    if sys.platform == 'win32' and not isinstance(loop, asyncio.ProactorEventLoop):
        if not loop.is_running():
            loop.close()
        # On Windows, the default event loop is SelectorEventLoop, which does
        # not support subprocesses. ProactorEventLoop should be used instead.
        # Source: https://docs.python.org/3/library/asyncio-subprocess.html
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    loop.set_default_executor(executor)
    # loop.set_debug(True)


@persistent
def kick_async_loop():
    """Perform one asyncio event loop iteration for Blender's timer."""

    global _stop_after_this_kick
    loop = get_event_loop()

    # Even when we want to stop, we always need to do one more
    # 'kick' to handle task-done callbacks.
    _stop_after_this_kick = False

    if loop.is_closed():
        log.warning('loop closed, stopping immediately.')
        return None

    all_tasks = None
    if bpy.app.version >= (2, 92):
        all_tasks = asyncio.all_tasks(loop)
    else:
        all_tasks = asyncio.Task.all_tasks()

    if not len(all_tasks):
        log.debug('no more scheduled tasks, stopping after this kick.')
        _stop_after_this_kick = True

    elif all(task.done() for task in all_tasks):
        log.debug('all %i tasks are done, fetching results and stopping after this kick.',
                  len(all_tasks))
        _stop_after_this_kick = True

        # Clean up circular references between tasks.
        gc.collect()

        for task_idx, task in enumerate(all_tasks):
            if not task.done():
                continue

            # noinspection PyBroadException
            try:
                res = task.result()
                log.debug('   task #%i: result=%r', task_idx, res)
            except asyncio.CancelledError:
                # No problem, we want to stop anyway.
                log.debug('   task #%i: cancelled', task_idx)
            except Exception:
                print('{}: resulted in exception'.format(task))
                traceback.print_exc()

            # for ref in gc.get_referrers(task):
            #     log.debug('      - referred by %s', ref)

    loop.stop()
    loop.run_forever()

    return ASYNC_LOOP_INTERVAL


def ensure_async_loop():
    global _stop_after_this_kick

    log.debug('Starting asyncio loop')
    _stop_after_this_kick = False

    if not bpy.app.timers.is_registered(kick_async_loop):
        bpy.app.timers.register(kick_async_loop, first_interval=ASYNC_LOOP_INTERVAL, persistent=True)


def erase_async_loop():
    log.debug('Erasing async loop')

    loop = get_event_loop()
    loop.stop()

    if bpy.app.timers.is_registered(kick_async_loop):
        bpy.app.timers.unregister(kick_async_loop)

    # loop synchronously for a bit so that the server can fully shut down. normally doesn't take long
    ticks = 0
    while ticks < 9000:
        kick_async_loop()

        if _stop_after_this_kick:
            break

        ticks = ticks + 1
    else:
        bpy.ops.pribambase.report(message_type='ERROR', message="Failed to close the connection. Sometimes that blocks new connections until blender restarts")
