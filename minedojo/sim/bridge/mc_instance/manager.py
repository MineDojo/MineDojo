import os
import time
import psutil
import socket
import logging
import threading
from typing import Optional
from contextlib import contextmanager

import Pyro4
import numpy as np

from .instance import MinecraftInstance

logger = logging.getLogger(__name__)


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class InstanceManager:
    """The Minecraft instance manager library. The instance manager can be used to allocate and safely terminate
    existing Malmo instances for training agents.

    MineRL Note: This object never needs to be explicitly invoked by the user of the MineRL library as the creation of
    one of the several MineRL environments will automatically query the InstanceManager to create a new instance.

    MineRL Note: In future versions of MineRL the instance manager will become its own daemon process which provides
    instance allocation capability using remote procedure calls.
    """

    MAXINSTANCES = None
    KEEP_ALIVE_PYRO_FREQUENCY = 5
    REMOTE = False

    _instance_pool = []
    _malmo_base_port = 9000
    _jdwp_base_port = 1044  # arbitrary. Used to find available ports for debugging.
    ninstances = 0
    X11_DIR = "/tmp/.X11-unix"
    managed = True

    seed = 42
    rng = np.random.default_rng(seed=seed)

    # this lock allows operating on the instance manager from instances (which
    # run in different worker threads)
    _im_lock: threading.Lock = threading.Lock()

    @classmethod
    def seed_manager(cls, seed: Optional[int]):
        cls.rng = np.random.default_rng(seed=seed)

    @classmethod
    def get_instance(cls, pid, instance_id=None):
        """
        Gets an instance from the instance manager. This method is a context manager
        and therefore when the context is entered the method yields a InstanceManager.Instance
        object which contains the allocated port and host for the given instance that was created.

        Yields:
            The allocated InstanceManager.Instance object.

        Raises:
            RuntimeError: No available instances or the maximum number of allocated instances reached.
            RuntimeError: No available instances and automatic allocation of instances is off.
        """
        if not instance_id:
            # Find an available instance.
            for inst in cls._instance_pool:
                if not inst.locked:
                    inst._acquire_lock(pid)

                    if hasattr(cls, "_pyroDaemon"):
                        cls._pyroDaemon.register(inst)

                    return inst
        # Otherwise make a new instance if possible
        if cls.managed:
            if cls.MAXINSTANCES is None or cls.ninstances < cls.MAXINSTANCES:
                instance_id = cls.ninstances if instance_id is None else instance_id

                cls.ninstances += 1
                # Make the status directory.

                inst = MinecraftInstance(
                    cls._get_valid_port(),
                    instance_id=instance_id,
                    seed=cls.rng.integers(low=0, high=2**31 - 1),
                )

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                # Check that not two instances share ports
                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                dup_ports = [i.uuid for i in cls._instance_pool if i.port == inst.port]
                if len(dup_ports) > 0:
                    # raise exception so we can identify the issue if it happens in experiments
                    raise RuntimeError(
                        f"There are instances with duplicated ports {dup_ports} vs {inst.uuid}"
                    )

                cls._instance_pool.append(inst)
                inst._acquire_lock(pid)

                # find a debugging port for this instance
                if os.getenv("JDWP_ENABLED", False):
                    InstanceManager.set_valid_jdwp_port_for_instance(instance=inst)
                    logger.info(
                        f"Instance {inst.uuid} reserved JDWP port {inst.jdwp_port}."
                    )

                if hasattr(cls, "_pyroDaemon"):
                    cls._pyroDaemon.register(inst)

                return inst

            else:
                raise RuntimeError(
                    "No available instances and max instances reached! :O :O"
                )
        else:
            raise RuntimeError("No available instances and managed flag is off")

    @classmethod
    def shutdown(cls):
        # Iterate over a copy of instance_pool because _stop removes from list
        # This is more time/memory intensive, but allows us to have a modular
        # stop function
        for inst in cls._instance_pool[:]:
            inst.release_lock()
            inst.kill()

    @classmethod
    @contextmanager
    def allocate_pool(cls, num):
        for _ in range(num):
            inst = MinecraftInstance(
                cls._get_valid_port(), seed=cls.rng.integers(low=0, high=2**31 - 1)
            )
            cls._instance_pool.append(inst)
        yield None
        cls.shutdown()

    @classmethod
    def add_existing_instance(cls, port):
        assert cls._is_port_taken(port), "No Malmo mod utilizing the port specified."
        instance = MinecraftInstance(
            port=port, existing=True, seed=cls.rng.integers(low=0, high=2**31 - 1)
        )
        cls._instance_pool.append(instance)
        cls.ninstances += 1
        return instance

    @classmethod
    def add_keep_alive(cls, _pid, _callback):
        logger.debug(
            f"Recieved keep-alive callback from client {_pid}. Starting thread."
        )

        def check_client_connected(client_pid, keep_alive_proxy):
            logger.debug(
                f"Client keep-alive connection monitor started for {client_pid}."
            )
            while True:
                time.sleep(InstanceManager.KEEP_ALIVE_PYRO_FREQUENCY)
                try:
                    keep_alive_proxy.call()
                except:
                    bad_insts = [
                        inst for inst in cls._instance_pool if inst.owner == client_pid
                    ]
                    for inst in bad_insts:
                        inst.close()

        keep_alive_thread = threading.Thread(
            target=check_client_connected, args=(_pid, _callback)
        )
        keep_alive_thread.setDaemon(True)
        keep_alive_thread.start()

    @staticmethod
    def _is_port_taken(port, address="0.0.0.0"):
        if psutil.MACOS or psutil.AIX:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind((address, port))
                taken = False
            except socket.error as e:
                if e.errno in [98, 10048, 48]:
                    taken = True
                else:
                    raise e

            s.close()
            return taken
        else:
            ports = [x.laddr.port for x in psutil.net_connections()]
            return port in ports

    @classmethod
    def _port_in_instance_pool(cls, port):
        # Ideally, this should be covered by other cases, but there may be delay
        # in when the ports get "used"
        for instance in cls._instance_pool:
            if port == instance.port or port == instance.jdwp_port:
                return True
        return False

    @classmethod
    def configure_malmo_base_port(cls, malmo_base_port):
        """Configure the lowest or base port for Malmo"""
        cls._malmo_base_port = malmo_base_port

    @classmethod
    def _get_valid_port(cls):
        malmo_base_port = cls._malmo_base_port
        port = (cls.ninstances % 5000) + malmo_base_port
        port += (17 * os.getpid()) % 3989
        while cls._is_port_taken(port) or cls._port_in_instance_pool(port):
            port += 1
        return port

    @classmethod
    def set_valid_jdwp_port_for_instance(cls, instance) -> None:
        """
        Find a valid port for JDWP (Java Debug Wire Protocol), so that the instance can be debugged
        with an attached debugger. The port is set in the instance, so that other instances can
        check whether the port is reserved.
        :param instance: Instance to find and port for, and where we will set the jdwp port.
        """
        # since we need to check whether other instances have ports claimed, we should find ports
        # for instances already in the pool
        assert (
            instance in cls._instance_pool
        ), "Attempted to find jdwp port for instance not in the pool."

        port = cls._jdwp_base_port
        last_port_to_check = port + 256  # do not try forever

        # this needs to be atomic, otherwise other threads checking for ports might grab the same
        # port
        with cls._im_lock:

            # find a port
            while cls._is_port_taken(port) or cls._port_in_instance_pool(port):
                port += 1
                if port >= last_port_to_check:
                    instance.jdwp_port = None
                    break

            # set the port in the instance before releasing the lock
            instance.jdwp_port = port

    @classmethod
    def is_remote(cls):
        return cls.REMOTE
