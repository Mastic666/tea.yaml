#!/usr/bin/python2
# coding: utf-8
import lurklib
import glob
import sys
import logging
import logging.handlers
import os

from os.path import basename, join


class Plugger(object):
    def __init__(self, bot, path):
        self.bot = bot
        if not path in sys.path:
            sys.path.append(os.path.join(os.getcwd(),path))
        self.path = path

    def load_plugins(self):
        for plugin in glob.glob("%s/*.py" % self.path):
            logging.debug("Loading %s" % plugin)
            self.load_plugin(basename(plugin), py=True)

    def load_plugin(self, name, py=False):
        # Is there ".py in name?
        if not py:
            name = name + ".py"

        logging.debug("Trying to load %s" % name)
        plug = __import__(name[:-3])
        plug.Plugin(self.bot)


class Bot(lurklib.Client):
    def __init__(self,
                server,
                admin,
                port=None,
                nick='lalal',
                user='lalala',
                real_name='lalilu',
                password=None,
                tls=False,
                tls_verify=False,
                encoding='UTF-8',
                hide_called_events=True,
                UTC=False,
                channel="#lalala",
                version="lala 0.1",
                debug=True,
                debugformat=
                "%(levelname)s %(filename)s: %(funcName)s:%(lineno)d %(message)s",
                log=True,
                logfolder="~/.lala/logs",
                plugins=['last', 'quotes', 'base'],
                nickserv=None
                ):

        self._admins = admin

        if log:
            logfolder = os.path.expanduser(logfolder)
            self._logfile = join(logfolder, "lala.log")
            if not os.path.exists(logfolder):
                os.makedirs(logfolder)
            self._logger = logging.getLogger("MessageLog")
            handler = logging.handlers.TimedRotatingFileHandler(
                    encoding="utf-8",
                    filename=self._logfile,
                    when="midnight")
            self._logger.setLevel(logging.INFO)
            handler.setFormatter(
                    logging.Formatter("%(asctime)s %(message)s",
                                      "%Y-%m-%d %H:%m"))
            self._logger.addHandler(handler)

        if debug:
            logging.basicConfig(format=debugformat, level=logging.DEBUG)

        self._channel = channel
        self._callbacks = {}
        self._join_callbacks = list()
        self._regexes = {}
        self._cbprefix = "!"
        self.__version__ = version
        self._nickserv_password = nickserv
        self.plugger = Plugger(self, "lala/plugins")
        for plugin in plugins:
            self.plugger.load_plugin(plugin)
        self.plugger.load_plugin("base")

        lurklib.Client.__init__(self,
                server = server,
                port = port,
                nick = nick,
                real_name = real_name,
                password = password,
                tls = tls,
                tls_verify = tls_verify,
                encoding = encoding,
                hide_called_events = hide_called_events,
                UTC = UTC
                )

    def on_connect(self):
        if self._nickserv_password:
            logging.debug("Identifying with %s" % self._nickserv_password)
            self.privmsg("NickServ", "identify %s" % self._nickserv_password)

    def on_privmsg(self, event):
        user = event[0][0]
        text = event[2]
        if event[1] == self.current_nick:
            channel = user
        else:
            channel = event[1]
        self._logger.info("%s: %s" % (user, text))
        try:
            if text.startswith(self._cbprefix):
                command = text.split()[0].replace(self._cbprefix, "")
                if command in self._callbacks:
                    self._callbacks[command](
                        self,  # bot
                        user,
                        channel,  # channel
                        text)

            for regex in self._regexes:
                match = regex.search(text)
                if match is not None:
                    self._regexes[regex](
                            self,
                            user,
                            channel,
                            text,
                            match)
        except (lurklib.exceptions._Exceptions.NotInChannel,
                lurklib.exceptions._Exceptions.NotOnChannel):
            # Some plugin tried to send to a channel it's not in
            # This should not happen, but anyway:
            pass
        # Catch TypeError: some command parameter was not correct
        # TODO Find a way to tell people about wrong parameters
        except TypeError, e:
            pass

    def on_notice(self, event):
        user = event[0][0]
        text = event[2]
        self._logger.info("NOTICE from %s: %s" % (user, text))

    def on_join(self, event):
        logging.debug("%s joined" % event[0][0])
        for cb in self._join_callbacks:
            cb(self, event)

    def on_ctcp(self, event):
        if event[2] == "VERSION":
            logging.debug("VERSION request from %s" % event[0][0])
            self.notice(event[0][0],
                        self.ctcp_encode("VERSION %s" % self.__version__))

    def on_quit(self, event):
        user = event[0][0]
        reason = event[1]
        self._logger.info("%s left: %s" % (user, reason))

    def register_callback(self, trigger, func):
        """ Adds func to the callbacks for trigger """
        logging.debug("Registering callback for %s" % trigger)
        self._callbacks[trigger] = func

    def register_join_callback(self, func):
        self._join_callbacks.append(func)

    def register_regex(self, regex, func):
        self._regexes[regex] = func

if __name__ == '__main__':
    bot = Bot()
    bot.mainloop()
