import sys
import threading
import time
from typing import Optional


class Color:
    black: 'Color'
    red: 'Color'
    green: 'Color'
    yellow: 'Color'
    blue: 'Color'
    magenta: 'Color'
    cyan: 'Color'
    white: 'Color'

    def __init__(self, code: int) -> None:
        self.__code: int = code

    @property
    def foreground(self) -> str:
        return f'\033[3{self.__code}m'

    @property
    def background(self) -> str:
        return f'\033[4{self.__code}m'


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
        self._is_tty: bool = sys.stdout.isatty()

        # style
        self.label: str = label

        if self._is_tty:
            self._color: str = color.foreground
            self._bar_fill: str = '█'
            self._bar_empty: str = '░'
            self._line_begin: str = '\r'
            self._line_end: str = ''

            self._esc_color_end: str = '\033[m'
            self._esc_hide_cursor: str = '\033[?25l'
            self._esc_show_cursor: str = '\033[?25h'
        else:
            self._color: str = ''
            self._bar_fill: str = '.'
            self._bar_empty: str = ' '
            self._line_begin: str = ''
            self._line_end: str = '\n'

            self._esc_color_end: str = ''
            self._esc_hide_cursor: str = ''
            self._esc_show_cursor: str = ''

        # state
        self._refresh_timeout: float = refresh_time_in_seconds
        self._bar_length: int = bar_length

        self._start_time: Optional[float] = None
        self._rendered_progress: float = -1.0
        self._progress: float = 0.0
        self._background_thread: Optional[threading.Timer] = None
        self._previous_update_length: int = 0

    def _timer_handle(self) -> None:
        self._update()
        self._background_thread = threading.Timer(self._refresh_timeout, self._timer_handle)
        self._background_thread.start()

    def _render(self, elapsed_time: float, eta: float, message: str = None) -> str:
        bar_fill_len = int(self._bar_length * self._progress)
        bar_text = (self._color +
                    (self._bar_fill * bar_fill_len) + (self._bar_empty * (self._bar_length - bar_fill_len)) +
                    self._esc_color_end)

        progress_text = f'{round(100.0 * self._progress, 1):.1f}%'.rjust(6)

        elapsed_time = int(round(elapsed_time))
        eta = int(round(eta))

        elapsed_text = f'{int(elapsed_time / 60):02d}:{elapsed_time % 60:02d}'
        eta_text = f'ETA {int(eta / 3600):02d}:{int(eta / 60) % 60:02d}:{eta % 60:02d}' if eta > 0 else None

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

    def _should_update(self) -> bool:
        if self._rendered_progress < 0 or self._is_tty:
            return True
        if self._progress == self._rendered_progress:
            return False
        if self._progress in (0, 1):
            return True

        return self._progress // 0.1 != self._rendered_progress // 0.1

    def _update(self, message: str = None) -> None:
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

    def start(self) -> None:
        self._start_time = time.time()
        self._timer_handle()

    def set_progress(self, progress: float) -> None:
        self._progress = min(1., max(0., progress))

    def cancel(self) -> None:
        if self._background_thread is not None:
            self._background_thread.cancel()
        sys.stdout.write(self._esc_show_cursor)

    def complete(self) -> None:
        if self._background_thread is not None:
            self._background_thread.cancel()
        self._progress = 1.0
        self._update()
        sys.stdout.write('\n')
        sys.stdout.write(self._esc_show_cursor)

    def abort(self, error: str = None) -> None:
        if self._background_thread is not None:
            self._background_thread.cancel()
        self._update(message=None if error is None else f' ERROR: {error}')
        sys.stdout.write('\n')
        sys.stdout.write(self._esc_show_cursor)
