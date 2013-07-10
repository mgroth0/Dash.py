import os
import sys
import time
import logging
import zipfile
import tarfile
import requests

try:
    import curses
    assert curses
except ImportError:
    curses = None

try:
    from cStringIO import StringIO
    assert StringIO
except ImportError:
    from io import StringIO


def download_and_extract(package, extract_path):
    name = package["name"]
    url = package["url"]
    type = package["type"]
    if type == 'git':
        logger.info("Cloning package %s" % name)
        os.system("git clone %s %s" % (url, extract_path))
        return

    logger.info("Downloading package %s" % name)
    f = StringIO()
    f.write(requests.get(url).content)
    f.seek(0)

    file = None

    if type == 'zip':
        file = zipfile.ZipFile(f)
    elif type == 'tar':
        file = tarfile.open(fileobj=f)

    file.extractall(extract_path)
    file.close()
    f.close()



logger = logging.getLogger("dash.py")


def enable_pretty_logging(level='info'):
    """Turns on formatted logging output as configured.

    This is called automatically by `parse_command_line`.
    """
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        # Set up color if we are in a tty and curses is installed
        color = False
        if curses and sys.stderr.isatty():
            try:
                curses.setupterm()
                if curses.tigetnum("colors") > 0:
                    color = True
            except Exception:
                pass
        channel = logging.StreamHandler()
        channel.setFormatter(_LogFormatter(color=color))
        logger.addHandler(channel)


class _LogFormatter(logging.Formatter):
    def __init__(self, color, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        self._color = color
        if color:
            # The curses module has some str/bytes confusion in
            # python3.  Until version 3.2.3, most methods return
            # bytes, but only accept strings.  In addition, we want to
            # output these strings with the logging module, which
            # works with unicode strings.  The explicit calls to
            # unicode() below are harmless in python2 but will do the
            # right conversion in python 3.
            fg_color = (curses.tigetstr("setaf") or
                        curses.tigetstr("setf") or "")
            if (3, 0) < sys.version_info < (3, 2, 3):
                fg_color = unicode(fg_color, "ascii")
            self._colors = {
                logging.DEBUG: unicode(curses.tparm(fg_color, 4),  # Blue
                    "ascii"),
                logging.INFO: unicode(curses.tparm(fg_color, 2),  # Green
                    "ascii"),
                logging.WARNING: unicode(curses.tparm(fg_color, 3),  # Yellow
                    "ascii"),
                logging.ERROR: unicode(curses.tparm(fg_color, 1),  # Red
                    "ascii"),
                }
            self._normal = unicode(curses.tigetstr("sgr0"), "ascii")

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        record.asctime = time.strftime(
            "%y%m%d %H:%M:%S", self.converter(record.created))
        prefix = '[%(levelname)1.1s %(asctime)s]' % record.__dict__
        if self._color:
            prefix = (self._colors.get(record.levelno, self._normal) +
                      prefix + self._normal)
        formatted = prefix + " " + record.message
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted = formatted.rstrip() + "\n" + record.exc_text
        return formatted.replace("\n", "\n    ")
