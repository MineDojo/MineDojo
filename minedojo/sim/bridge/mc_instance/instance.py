import os
import sys
import uuid
import time
import struct
import psutil
import socket
import atexit
import tempfile
import threading
import functools
import subprocess
import collections

import Pyro4
import locale
import shutil
import logging

from ...bridge import utils as U

__all__ = ["MinecraftInstance"]


logger = logging.getLogger(__name__)
MALMO_VERSION = "0.37.0"
MC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "Malmo",
    "Minecraft",
)
SCHEMAS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "Malmo",
    "Schemas",
)


@Pyro4.expose
class MinecraftInstance:
    """
    A subprocess wrapper which maintains a reference to a minecraft subprocess
    and also allows for stable closing and launching of such subprocesses
    across different platforms.

    The Minecraft instance class works by launching two subprocesses:
    the Malmo subprocess, and a watcher subprocess with access to
    the process IDs of both the parent process and the Malmo subprocess.
    If the parent process dies, it will kill the subprocess, and then itself.

    This scheme has a single failure point of the process dying before the watcher process is launched.
    """

    MAX_PIPE_LENGTH = 500

    def __init__(self, port=None, existing=False, seed=None, instance_id=None):
        """
        Launches the subprocess.
        """
        self.running = False
        self._starting = True
        self.minecraft_process = None
        self.watcher_process = None
        self.xml = None
        self.role = None
        self._client_socket = None
        self._port = port
        self._jdwp = None
        self._host = "localhost"
        self.locked = False
        self.uuid = str(uuid.uuid4()).replace("-", "")[:6]
        self.existing = existing
        self.minecraft_dir = None
        self.instance_dir = None
        self.owner = None
        self._had_to_clean = False
        self.instance_id = instance_id
        self._seed = seed
        self._target_port = port

        self._setup_logging()

    # class-wide Pyro4 exposes are not encouraged as of new versions
    @Pyro4.expose
    @property
    def had_to_clean(self):
        return self._had_to_clean

    @Pyro4.expose
    @had_to_clean.setter
    def had_to_clean(self, value):
        self._had_to_clean = value

    @Pyro4.expose
    @property
    def client_socket(self):
        return self._client_socket

    @Pyro4.expose
    @client_socket.setter
    def client_socket(self, value):
        # Not ideal as you should not be trying to serialize
        # sockets. However the code does set the socket to
        # Nones at times, so lets allow it.
        self._client_socket = value

    def create_instance_socket(self, socktime):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(socktime)
        sock.connect((self.host, self.port))
        self.client_socket = sock

    def client_socket_send_message(self, msg):
        U.send_message(self.client_socket, msg)

    def client_socket_recv_message(self):
        return U.recv_message(self.client_socket)

    def client_socket_close(self):
        self.client_socket.close()
        self.client_socket = None

    def client_socket_shutdown(self, param):
        self.client_socket.shutdown(param)
        self.client_socket = None

    def has_client_socket(self):
        return self.client_socket is not None

    @property
    def actor_name(self):
        return f"actor{self.role}"

    def launch(self, daemonize=False, replaceable=True):
        from ..utils import watchdog
        from .manager import InstanceManager

        port = self._target_port
        self._starting = True

        if not self.existing:
            if not port:
                port = InstanceManager._get_valid_port()

            self.instance_dir = tempfile.mkdtemp()
            self.minecraft_dir = os.path.join(self.instance_dir, "Minecraft")
            shutil.copytree(
                os.path.join(MC_DIR),
                self.minecraft_dir,
                ignore=shutil.ignore_patterns("**.lock"),
            )
            shutil.copytree(
                os.path.join(SCHEMAS_DIR),
                os.path.join(self.instance_dir, "Schemas"),
            )

            # 0. Get PID of launcher.
            parent_pid = os.getpid()
            # 1. Launch minecraft process
            self.minecraft_process = self._launch_minecraft(
                port,
                self.minecraft_dir,
                replaceable=replaceable,
            )

            # 2. Create a watcher process to ensure things get cleaned up
            if not daemonize:
                # 2. Create a watcher process to ensure things get cleaned up
                self.watcher_process = watchdog.launch(
                    parent_pid, self.minecraft_process.pid, self.instance_dir
                )

            # wait until Minecraft process has output "CLIENT enter state: DORMANT"
            lines = []
            client_ready = False
            server_ready = False

            while True:
                mine_log_encoding = locale.getpreferredencoding(False)
                line = self.minecraft_process.stdout.readline().decode(
                    mine_log_encoding
                )

                if os.environ.get("MINEDOJO_DEBUG_LOG", False):
                    # Print Java logs to console
                    print(line.strip("\n"))

                # Check for failures and print useful messages!
                # _check_for_launch_errors(line)

                if not line:
                    # IF THERE WAS AN ERROR STARTING THE MC PROCESS
                    # Print the whole logs!
                    error_str = ""
                    for l in lines:
                        spline = "\n".join(l.split("\n")[:-1])
                        self._logger.error(spline)
                        error_str += spline + "\n"
                    # Throw an exception!
                    raise EOFError(
                        error_str
                        + "\n\nMinecraft process finished unexpectedly. There was an error with Malmo."
                    )

                lines.append(line)
                self._log_heuristic("\n".join(line.split("\n")[:-1]))

                MALMOENVPORTSTR = "***** Start MalmoEnvServer on port "
                port_received = MALMOENVPORTSTR in line
                if port_received:
                    self._port = int(line.split(MALMOENVPORTSTR)[-1].strip())

                client_ready = "CLIENT enter state: DORMANT" in line
                server_ready = "SERVER enter state: DORMANT" in line

                if client_ready:
                    break

            if not self.port:
                raise RuntimeError(
                    "Malmo failed to start the MalmoEnv server! Check the logs from the Minecraft process."
                )
            self._logger.info("Minecraft process ready")

            if port != self._port:
                self._logger.warning(
                    f"Tried to launch Minecraft on port {port} but that port was taken, instead Minecraft is using port {self.port}."
                )

            # suppress entire output, otherwise the subprocess will block
            # NB! there will be still logs under Malmo/Minecraft/run/logs
            # FNULL = open(os.devnull, 'w')
            # launch a logger process
            def log_to_file(logdir):
                if not os.path.exists(os.path.join(logdir, "logs")):
                    os.makedirs((os.path.join(logdir, "logs")))

                file_path = os.path.join(
                    logdir, "logs", f"mc_{self._target_port - 9000}.log"
                )

                logger.info(f"Logging output of Minecraft to {file_path}")

                mine_log = open(file_path, "wb+")
                mine_log.truncate(0)
                mine_log_encoding = locale.getpreferredencoding(False)

                try:
                    while self.running:
                        line = self.minecraft_process.stdout.readline()
                        if not line:
                            break

                        try:
                            linestr = line.decode(mine_log_encoding)
                        except UnicodeDecodeError:
                            mine_log_encoding = locale.getpreferredencoding(False)
                            logger.error(
                                "UnicodeDecodeError, switching to default encoding"
                            )
                            linestr = line.decode(mine_log_encoding)

                        if os.environ.get("MINEDOJO_DEBUG_LOG", False):
                            # Print Java logs to console
                            print(linestr.strip("\n"))

                        linestr = "\n".join(linestr.split("\n")[:-1])
                        # some heuristics to figure out which messages
                        # need to be elevated in logging level
                        # "   at " elevation is related to logging exception's stacktrace
                        self._log_heuristic(linestr)
                        mine_log.write(line)
                        mine_log.flush()
                finally:
                    mine_log.close()

            logdir = os.environ.get("MALMO_MINECRAFT_OUTPUT_LOGDIR", ".")
            self.running = True
            self._logger_thread = threading.Thread(
                target=functools.partial(log_to_file, logdir=logdir)
            )
            self._logger_thread.setDaemon(True)
            self._logger_thread.start()
            self._starting = False

        else:
            assert port is not None, "No existing port specified."
            self._port = port
            self._starting = False
            self.running = True

        # Make a hook to kill
        if not daemonize:
            atexit.register(lambda: self._destruct())

    def kill(self):
        """
        Kills the process (if it has been launched.)
        """
        self._destruct()
        pass

    def close(self):
        """Closes the object."""
        self._destruct(should_close=True)

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def jdwp_port(self):
        """
        JDWP (Java Debug Wire Protocol) port, if any, so the instance can be debugged with an
        attached debugger.
        """
        return self._jdwp

    @jdwp_port.setter
    def jdwp_port(self, port):
        """
        JDWP (Java Debug Wire Protocol) port, if any, so the instance can be debugged with an
        attached debugger.
        :param port: Port to set (0 or None to disable remote debugging).
        """
        self._jdwp = port

    def get_output(self):
        while self.running or self._starting:
            try:
                level, line = self._output_stream.pop()
                return (
                    (line.levelno, line.getMessage(), line.name),
                    self.running or self._starting,
                )
            except IndexError:
                time.sleep(0.5)
        else:
            return None, False

    def _setup_logging(self):
        # Set up an output stream handler.
        self._logger = logging.getLogger(f"{__name__}.instance.{self.uuid}")
        self._output_stream = collections.deque(maxlen=self.MAX_PIPE_LENGTH)
        for level in [logging.DEBUG]:
            handler = U.QueueLogger(self._output_stream)
            handler.setLevel(level)
            self._logger.addHandler(handler)

    ###########################
    ##### PRIVATE METHODS #####
    ###########################
    def _launch_minecraft(self, port, minecraft_dir, replaceable=True):
        """Launch Minecraft listening for malmoenv connections.
        Args:
            port:  the TCP port to listen on.
            installdir: the install dir name. Defaults to MalmoPlatform.
            Must be same as given (or defaulted) in download call if used.
            replaceable: whether or not to automatically restart Minecraft.
        Asserts:
            that the port specified is open.
        """
        launch_script = "launchClient.sh"
        if os.name == "nt":
            raise ValueError("TODO")

        launch_script = os.path.join(minecraft_dir, launch_script)
        rundir = os.path.join(minecraft_dir, "run")

        cmd = [launch_script, "-port", str(port), "-env", "-runDir", rundir]
        if self._seed:
            cmd += ["-seed", str(self._seed)]

        # add jdwp port if any set
        if self.jdwp_port:
            cmd += ["-jvm_debug_port", str(self.jdwp_port)]

        self._logger.info("Starting Minecraft process: " + str(cmd))

        if replaceable:
            cmd.append("-replaceable")
        preexec_fn = (
            os.setsid
            if "linux" in str(sys.platform) or sys.platform == "darwin"
            else None
        )
        minecraft_process = psutil.Popen(
            cmd,
            cwd=MC_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            # use process group, see http://stackoverflow.com/a/4791612/18576
            preexec_fn=preexec_fn,
        )
        return minecraft_process

    @staticmethod
    def _kill_minecraft_via_malmoenv(host, port):
        """Use carefully to cause the Minecraft service to exit (and hopefully restart)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((host, port))
            U.send_message(sock, ("<MalmoEnv" + MALMO_VERSION + "/>").encode())

            U.send_message(sock, ("<Exit>NOW</Exit>").encode())
            reply = U.recv_message(sock)
            (ok,) = struct.unpack("!I", reply)
            sock.close()
            return ok == 1
        except Exception as e:
            logger.error(
                f"Attempted to send kill command to minecraft process and failed with exception {e}"
            )
            return False

    def __del__(self):
        """
        On destruction of this instance kill the child.
        """
        self._destruct()

    def _destruct(self, should_close=False):
        """
        Do our best as the parent process to destruct and kill the child + watcher.
        """
        from ..utils import watchdog
        from .manager import InstanceManager

        if (self.running or should_close) and not self.existing:
            self.running = False
            self._starting = False

            # Wait for the process to start.
            time.sleep(1)
            if self._kill_minecraft_via_malmoenv(self.host, self.port):
                # Let the minecraft process term on its own terms.
                time.sleep(2)

            # Now lets try and end the process if anything is lying around
            watchdog.reap_process_and_children(self.minecraft_process)

            # kill the minecraft process and its subprocesses
            try:
                shutil.rmtree(self.instance_dir)
            except:
                print("Failed to delete the temporary minecraft directory.")

            if self in InstanceManager._instance_pool:
                InstanceManager._instance_pool.remove(self)
                self.release_lock()
        pass

    def __repr__(self):
        return f"Malmo[{self.role}:{self.uuid}, proc={self.minecraft_process.pid if not self.existing else 'EXISTING'}, addr={self.host}:{self.port}, locked={self.locked}]"

    def _acquire_lock(self, owner=None):
        self.locked = True
        self.owner = owner

    def release_lock(self):
        self.locked = False
        self.owner = None

    def _log_heuristic(self, msg):
        """
        Log the message, heuristically determine logging level based on the
        message content
        """
        if (
            "STDERR" in msg
            or "ERROR" in msg
            or "Exception" in msg
            or "    at " in msg
            or msg.startswith("Error")
        ) and ("connection closed, likely by peer" not in msg):
            self._logger.error(msg)
        elif "WARN" in msg:
            self._logger.warning(msg)
        elif "LOGTOPY" in msg:
            self._logger.info(msg)
        else:
            self._logger.debug(msg)
