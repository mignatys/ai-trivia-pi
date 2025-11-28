"""
utils.py
--------
Contains utility classes and functions used across the application,
such as a reusable, interruptible timer.
"""

import threading
from logger import log

class Timer:
    """
    A reusable, interruptible timer that runs a callback function on a
    separate thread after a specified duration.
    """
    def __init__(self, duration_sec, callback, *args, **kwargs):
        self.duration_sec = duration_sec
        self.callback = callback
        self.args = args
        self.kwargs = kwargs
        self._timer_thread = None
        self._is_running = False
        self._finished = threading.Event()

    def _run(self):
        """The target function for the timer thread."""
        self._is_running = True
        # Wait for the duration. The wait can be interrupted by the cancel method.
        # The finished.wait() returns True if the event was set (i.e., cancelled)
        # and False if it timed out.
        was_cancelled = self._finished.wait(timeout=self.duration_sec)
        
        self._is_running = False
        
        # If the timer was not cancelled, run the callback.
        if not was_cancelled:
            log.debug(f"Timer of {self.duration_sec}s finished. Executing callback.")
            self.callback(*self.args, **self.kwargs)

    def start(self):
        """Starts the timer."""
        if self._is_running:
            log.warn("Timer is already running. Cannot start again.")
            return
            
        # Reset the event in case this timer is being reused
        self._finished.clear()
        
        self._timer_thread = threading.Thread(target=self._run, daemon=True)
        self._timer_thread.start()
        log.debug(f"Timer started for {self.duration_sec} seconds.")

    def cancel(self):
        """Cancels the timer if it is running."""
        if self._is_running:
            # Set the event to signal the waiting thread to wake up and exit
            self._finished.set()
            log.debug("Timer cancelled.")
        
    def is_running(self):
        """Returns True if the timer is currently active."""
        return self._is_running
