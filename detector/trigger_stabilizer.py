"""Time-based trigger confirmation, independent of camera frame rate."""

DEFAULT_SETTINGS = {
    'confirm_ms': 650, 'hold_ms': 1800, 'neutral_ms': 2600,
    'confidence': 0.72,
}


class TriggerStabilizer:
    def __init__(self, settings=None):
        self.settings = dict(DEFAULT_SETTINGS)
        self.configure(settings or {})
        self.reset()

    def configure(self, settings):
        self.settings.update(settings)
        self.candidate = None
        self.candidate_since = None

    def reset(self):
        self.current = 'neutral'
        self.candidate = None
        self.candidate_since = None
        self.last_seen = None
        self.last_switch = None

    def update(self, trigger, now_ms):
        """Return a newly confirmed label, or None to keep the current image."""
        if trigger and trigger != 'neutral':
            self.last_seen = now_ms
        else:
            trigger = 'neutral'
            if self.last_seen is None:
                self.last_seen = now_ms
            if now_ms - self.last_seen < self.settings['neutral_ms']:
                self.candidate = None
                self.candidate_since = None
                return None
        if trigger == self.current:
            self.candidate = None
            self.candidate_since = None
            return None
        if trigger != self.candidate:
            self.candidate = trigger
            self.candidate_since = now_ms
            return None
        if now_ms - self.candidate_since < self.settings['confirm_ms']:
            return None
        if self.last_switch is not None and now_ms - self.last_switch < self.settings['hold_ms']:
            return None
        self.current = trigger
        self.last_switch = now_ms
        self.candidate = None
        self.candidate_since = None
        return trigger
