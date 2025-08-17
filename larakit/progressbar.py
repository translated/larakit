import sys
import threading
import time


class Color:
    black: 'Color' = None
    red: 'Color' = None
    green: 'Color' = None
    yellow: 'Color' = None
    blue: 'Color' = None
    magenta: 'Color' = None
    cyan: 'Color' = None
    white: 'Color' = None

    def __init__(self, code: int) -> None:
        self.__code: int = code

    @property
    def foreground(self):
        return '\033[3%dm' % self.__code

    @property
    def background(self):
        return '\033[4%dm' % self.__code


Color.black = Color(0)
Color.red = Color(1)
Color.green = Color(2)
Color.yellow = Color(3)
Color.blue = Color(4)
Color.magenta = Color(5)
Color.cyan = Color(6)
Color.white = Color(7)


class Progressbar:
    def __init__(self, label: str = None,
                 bar_length: int = 40, refresh_time_in_seconds: float = 1., color: Color = Color.white):
        self._is_tty = sys.stdout.isatty()

        # style
        self.label: str = label

        if self._is_tty:
            self._color = color.foreground
            self._bar_fill = '█'
            self._bar_empty = '░'
            self._line_begin = '\r'
            self._line_end = ''

            self._esc_color_end = '\033[m'
            self._esc_hide_cursor = '\033[?25l'
            self._esc_show_cursor = '\033[?25h'
        else:
            self._color = ''
            self._bar_fill = '.'
            self._bar_empty = ' '
            self._line_begin = ''
            self._line_end = '\n'

            self._esc_color_end = ''
            self._esc_hide_cursor = ''
            self._esc_show_cursor = ''

        # state
        self._refresh_timeout = refresh_time_in_seconds
        self._bar_length = bar_length

        self._start_time = None
        self._rendered_progress = -1.0
        self._progress = 0.0
        self._background_thread = None
        self._previous_update_length = 0

    def _timer_handle(self):
        self._update()
        self._background_thread = threading.Timer(self._refresh_timeout, self._timer_handle)
        self._background_thread.start()

    def _render(self, elapsed_time, eta, message=None):
        bar_fill_len = int(self._bar_length * self._progress)
        bar_text = (self._color +
                    (self._bar_fill * bar_fill_len) + (self._bar_empty * (self._bar_length - bar_fill_len)) +
                    self._esc_color_end)

        progress_text = '{:.1f}%'.format(round(100.0 * self._progress, 1)).rjust(6)

        elapsed_text = '%02d:%02d' % (int(elapsed_time / 60), elapsed_time % 60)
        eta_text = 'ETA %02d:%02d:%02d' % (int(eta / 3600), int(eta / 60) % 60, eta % 60) if eta > 0 else None

        label = None
        if self.label is not None:
            label = '- ' + self.label

            if self._progress < 1:
                label += '...'
            else:
                label += ' completed.'

        message = None if message is None else ' ' + message

        elements = [progress_text, bar_text, elapsed_text, eta_text, label, message]
        return self._line_begin + ' '.join(x for x in elements if x is not None) + self._line_end

    def _should_update(self):
        if self._rendered_progress < 0 or self._is_tty:
            return True
        if self._progress == self._rendered_progress:
            return False
        if self._progress == 0 or self._progress == 1:
            return True

        return self._progress // 0.1 != self._rendered_progress // 0.1

    def _update(self, message=None):
        if message is None and not self._should_update():
            return

        elapsed = time.time() - self._start_time
        eta = elapsed / self._progress - elapsed if self._progress > 0 else 0

        update_string = self._render(elapsed, eta, message) + self._esc_hide_cursor

        if self._is_tty:
            if len(update_string) < self._previous_update_length:
                update_string = update_string + ' ' * (self._previous_update_length - len(update_string))
            self._previous_update_length = len(update_string)

        sys.stdout.write(update_string)
        sys.stdout.flush()

        self._rendered_progress = self._progress

    def start(self):
        self._start_time = time.time()
        self._timer_handle()

    def set_progress(self, progress: float) -> None:
        self._progress = progress

    def cancel(self):
        self._background_thread.cancel()
        sys.stdout.write(self._esc_show_cursor)

    def complete(self):
        self._background_thread.cancel()
        self._progress = 1.0
        self._update()
        sys.stdout.write('\n')
        sys.stdout.write(self._esc_show_cursor)

    def abort(self, error: str = None):
        self._background_thread.cancel()
        self._update(message=None if error is None else (' ERROR: %s' % error))
        sys.stdout.write('\n')
        sys.stdout.write(self._esc_show_cursor)
