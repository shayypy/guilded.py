"""
The MIT License (MIT)

Copyright (c) 2021-present windowsboy111, shay (shayypy)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

------------------------------------------------------------------------------

This project includes code from https://github.com/Rapptz/discord.py, which is
available under the MIT license:

The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""
import asyncio
import datetime
import inspect
import logging
import sys
import traceback

import aiohttp

import guilded
from guilded.utils import sleep_until
from guilded.utils.backoff import ExponentialBackoff

logger = logging.getLogger(__name__)


class Loop:
    """
    A background task helper/interface.

    It is recommended to create a loop through `loop()`.
    """

    def __init__(self, fn, *, seconds, hours, minutes, count, reconnect, loop):
        self.fn = fn
        self.reconnect = reconnect
        self.loop = loop
        self.count = count
        self._current_loop = 0
        self._task = None
        self._injected = None
        self._valid_exception = (
            OSError,
            guilded.HTTPException,
            aiohttp.ClientError,
            asyncio.TimeoutError,
        )
        self._before_loop = None
        self._after_loop = None
        self._cancelled = False
        self._failed = False
        self._stop_next_iteration = False

        self.change_interval(seconds=seconds, minutes=minutes, hours=hours)
        self._last_iteration_failed = False
        self._last_iteration = None
        self._next_iteration = None

    async def _call_loop_function(self, name, *args, **kwargs):
        fn = getattr(self, "_" + name)
        if fn is None:
            return

        if self._injected is not None:
            ret = fn(self._injected, *args, **kwargs)
        else:
            ret = fn(*args, **kwargs)
        if asyncio.iscoroutinefunction(fn):
            ret = await ret

    async def _loop(self, *args, **kwargs):
        backoff = ExponentialBackoff()
        await self._call_loop_function("before_loop")
        self._last_iteration_failed = False
        self._next_iteration = datetime.datetime.now(datetime.timezone.utc)
        try:
            await asyncio.sleep(0)  # allows canceling in before_loop
            while True:
                if not self._last_iteration_failed:
                    self._last_iteration = self._next_iteration
                    self._next_iteration = self._get_next_sleep_time()
                try:
                    ret = self.fn(*args, **kwargs)
                    if asyncio.iscoroutinefunction(self.fn):
                        await ret
                    self._last_iteration_failed = False
                    now = datetime.datetime.now(datetime.timezone.utc)
                    if now > self._next_iteration:
                        self._next_iteration = now
                except self._valid_exception:
                    self._last_iteration_failed = True
                    if not self.reconnect:
                        raise
                    await asyncio.sleep(backoff.delay())
                else:
                    await sleep_until(self._next_iteration)

                    if self._stop_next_iteration:
                        return
                    self._current_loop += 1
                    if self._current_loop == self.count:
                        break
        except asyncio.CancelledError:
            self._cancelled = True
            raise
        except Exception as exc:
            self._failed = True
            await self._call_loop_function("error", exc)
            raise exc
        finally:
            await self._call_loop_function("after_loop")
            self._cancelled = False
            self._current_loop = 0
            self._stop_next_iteration = False
            self._failed = False

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        copy = Loop(
            self.fn,
            seconds=self.seconds,
            hours=self.hours,
            minutes=self.minutes,
            count=self.count,
            reconnect=self.reconnect,
            loop=self.loop,
        )
        copy._injected = obj
        copy._before_loop = self._before_loop
        copy._after_loop = self._after_loop
        copy._error = self._error
        setattr(obj, self.fn.__name__, copy)
        return copy

    @property
    def current_loop(self):
        """
        Retrieve the number of times the loop has ran

        Returns
        -------
        int
            The current iteration of the loop.
        """
        return self._current_loop

    @property
    def next_iteration(self):
        """
        Returns
        -------
        Optional[:class:`datetime.datetime`]
            When the next iteration of the loop will occur.
        """
        if self._task is None:
            return None
        elif self._task and self._task.done() or self._stop_next_iteration:
            return None
        return self._next_iteration

    async def __call__(self, *args, **kwargs):
        """
        Calls the internal callback that the task holds.

        *args: positional arguments
        **kwargs: keyword arguments

        Returns
        -------
        Any
            The return value of the callback.
        """

        if self._injected is not None:
            args = (self._injected, *args)

        ret = self.fn(*args, **kwargs)
        if asyncio.iscoroutinefunction(self.fn):
            ret = await ret

        return ret

    def start(self, *args, **kwargs):
        """
        Starts the internal task in the event loop.

        *args: posiitonal arguments
        **kwargs: keyword arguments

        You may call this function with the arguments for the callback.

        Returns
        -------
        asyncio.Task
            The task that has been created.

        Raises
        ------
        RuntimeError
            A task has already been launched and is running.
        """

        if self._task is not None and not self._task.done():
            raise RuntimeError(
                "Task is already launched and is not completed."
            )

        if self._injected is not None:
            args = (self._injected, *args)

        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self._task = self.loop.create_task(self._loop(*args, **kwargs))
        return self._task

    def stop(self):
        """
        Gracefully stops the task from running.

        Unlike `cancel()`, this allows the task to finish its current
        iteration before gracefully exiting.

        Note
        ----
        If the internal function raises an error that can be handled
        before finishing then it will retry until it succeeds.

        If this is undesirable, either remove the error handling before
        stopping via `clear_exception_types()` or use `cancel()` instead.
        """
        if self._task and not self._task.done():
            self._stop_next_iteration = True

    def _can_be_cancelled(self):
        return (
            not self._cancelled
            and self._task
            and not self._task.done()
        )

    def cancel(self):
        """Cancels the internal task, if it is running."""
        if self._can_be_cancelled():
            self._task.cancel()

    def restart(self, *args, **kwargs):
        """
        A convenience method to restart the internal task.

        Note
        ----
        Due to the way this function works, the task is not
        returned like `start()`.

        Parameters
        ------------
        *args
            The arguments to to use.
        **kwargs
            The keyword arguments to use.
        """

        def restart_when_over(fut, *, args=args, kwargs=kwargs):
            self._task.remove_done_callback(restart_when_over)
            self.start(*args, **kwargs)

        if self._can_be_cancelled():
            self._task.add_done_callback(restart_when_over)
            self._task.cancel()

    def add_exception_type(self, *exceptions):
        """Adds exception types to be handled during the reconnect logic.

        By default the exception types handled are those handled by
        `Client.connect`, which includes a lot of internet disconnection
        errors.

        This function is useful if you're interacting with a 3rd party library
        that raises its own set of exceptions.

        Parameters
        ----------
        *exceptions: Type[BaseException]
            An argument list of exception classes to handle.
        Raises
        ------
        TypeError
            An exception passed is not inherited from `BaseException`.
        """

        for exc in exceptions:
            if not inspect.isclass(exc):
                raise TypeError(f"{exc!r} must be a class.")
            if not issubclass(exc, BaseException):
                raise TypeError(f"{exc!r} must inherit from BaseException.")

        self._valid_exception = (*self._valid_exception, *exceptions)

    def clear_exception_types(self):
        """
        Removes all exception types that are handled.

        Note
        ----
        This operation obviously cannot be undone!
        """
        self._valid_exception = tuple()

    def remove_exception_type(self, *exceptions):
        """
        Removes exception types from being handled during the reconnect logic.

        Parameters
        ----------
        *exceptions: Type[BaseException]
            An argument list of exception classes to handle.

        Returns
        -------
        bool
            Whether all exceptions were successfully removed.
        """
        old_length = len(self._valid_exception)
        self._valid_exception = tuple(
            x for x in self._valid_exception if x not in exceptions
        )
        return len(self._valid_exception) == old_length - len(exceptions)

    def get_task(self):
        """
        Fetches the internal task or `None` if there isn't one running.

        Returns
        -------
        Optional[asyncio.Task]
            The internal task or None
        """
        return self._task

    def is_being_cancelled(self):
        """
        Whether the task is being cancelled.

        Returns
        -------
        bool
        """
        return self._cancelled

    def failed(self):
        """
        Whether the internal task has failed

        Returns
        -------
        bool
        """
        return self._failed

    def is_running(self):
        """:class:`bool`: Check if the task is currently running.
        .. versionadded:: 1.4
        """
        return not bool(self._task.done()) if self._task else False

    async def _error(self, *args):
        exception = args[-1]
        print(
            "Unhandled exception in internal background task "
            f"{self.fn.__name__!r}.",
            file=sys.stderr,
        )
        traceback.print_exception(
            type(exception),
            exception,
            exception.__traceback__,
            file=sys.stderr,
        )

    def before_loop(self, fn):
        """
        A decorator that registers a function to be called before the loop
        starts running.

        This is useful if you want to wait for some bot state before the loop
        starts, such as `Client.wait_until_ready`.
        The function must take no arguments (except `self` in a class).

        Parameters
        ----------
        fn : Callable
            The function to register before the loop runs.

        Raises
        -----
        TypeError
            `fn` is not `callable()`.
        """

        if not callable(fn):
            raise TypeError(
                f"Expected callable, received {type(fn)!r}."
            )

        self._before_loop = fn
        return fn

    def after_loop(self, fn):
        """
        A decorator that register a function to be called after the loop
        finished running.

        The function must take no arguments (except `self` in a class).

        Note
        ----
            This function is called even during cancellation. If it is
            desirable to tell apart whether something was cancelled or not,
            check to see whether `is_being_cancelled()` is `True` or not.

        Parameters
        ----------
        fn : Callable
            The function to register after the loop finishes.

        Raises
        -----
        TypeError
            `fn` is not `callable()`.
        """

        if not callable(fn):
            raise TypeError(
                f"Expected function function, received {type(fn).__name__!r}."
            )

        self._after_loop = fn
        return fn

    def error(self, fn):
        """
        A decorator that registers a function to be called if the task
        encounters an unhandled exception.

        The function must take only one argument the exception raised
        (except `self` in a class).
        By default this prints to `sys.stderr`, however
        it could be overridden to have a different implementation.

        Parameters
        ----------
        fn : Callable
            The function to register in the event of an unhandled exception.
        Raises
        -------
        TypeError
            `fn` is not `callable()`.
        """
        if not callable(fn):
            raise TypeError(
                f"Expected function, received {type(fn).__name__!r}."
            )

        self._error = fn
        return fn

    def _get_next_sleep_time(self):
        return self._last_iteration + datetime.timedelta(seconds=self._sleep)

    def change_interval(self, *, seconds=0, minutes=0, hours=0):
        """
        Changes the interval for the sleep time.

        Note
        ----
        This only applies on the next loop iteration. If it is desirable for
        the change of interval to be applied right away, `cancel()` the task.

        Parameters
        ----------
        seconds : float
            The number of seconds between every iteration.
        minutes : float
            The number of minutes between every iteration.
        hours : float
            The number of hours between every iteration.

        Raises
        ------
        ValueError
            An invalid value was given.
        """

        sleep = seconds + (minutes * 60.0) + (hours * 3600.0)
        if sleep < 0:
            raise ValueError(
                "Total number of seconds cannot be less than zero."
            )

        self._sleep = sleep
        self.seconds = seconds
        self.hours = hours
        self.minutes = minutes


def loop(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    count: float = None,
    reconnect: bool = True,
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop(),
):
    """
    A decorator that schedules a task in the background for you with
    optional reconnect logic.

    Functions or coroutines can be supplied.

    Parameters
    ----------
    seconds : float, optional
        The number of seconds between every iteration, by default 0
    minutes : float, optional
        The number of minutes between every iteration, by default 0
    hours : float, optional
        The number of hours between every iteration, by default 0
    count : float, optional
        The number of loops to do, by default None (infinite)
    reconnect : bool, optional
        Whether to handle errors and restart the task using an exponential
        back-off algorithm similar to the one used in
        `Client.connect`, by default True
    loop : asyncio.AbstractEventLoop, optional
        The loop for registering tasks, by default `asyncio.get_event_loop()`

    Returns
    -------
    Loop

    Raises
    ------
    ValueError
        An invalid value was given.
    TypeError
        The function was not callable.
    """
    if count and count < 1:
        raise ValueError("count must be greater than 0 or None.")

    def deco(fn):
        if not callable(fn):
            raise TypeError(f"Expected Callables, not {type(fn).__name__!r}.")
        kws = {
            "seconds": seconds,
            "minutes": minutes,
            "hours": hours,
            "count": count,
            "reconnect": reconnect,
            "loop": loop,
        }
        return Loop(fn, **kws)

    return deco
