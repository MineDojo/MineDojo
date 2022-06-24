import os
import json
import time
import struct
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, NamedTuple, Dict

import numpy as np
from lxml import etree

from ..mc_instance import InstanceManager, MinecraftInstance
from ..utils import retry


MALMO_VERSION = "0.37.0"
# Time to wait before raising an exception (high value because some operations we wait on are very slow)
MAX_WAIT = 600

logger = logging.getLogger(__name__)


class StepTuple(NamedTuple):
    """
    step_success: whether this MC client step is successful
    raw_obs: if step successful, will be a dict (key is player index) of raw obs dict. Otherwise, will be none
    """

    step_success: bool
    raw_obs: Optional[Dict[int, dict]]


class BridgeEnv:
    """
    Bridge MineDojo sim and MineCraft java world.
    Not necessarily need to be a gym.env sub-class.
    """

    MALMO_VERSION = MALMO_VERSION
    # specifies if turnkey and info are included in message.
    STEP_OPTIONS = 0
    # After this much time a socket exception will be thrown.
    SOCKTIME = 60.0 * 4

    def __init__(
        self,
        *,
        agent_count: int = 1,
        is_fault_tolerant: bool = True,
        seed: Optional[int] = None,
    ):
        assert agent_count == 1, "TODO"
        self._agent_count = agent_count
        self._rng = np.random.default_rng(seed=seed)
        self._instances: List[MinecraftInstance] = []
        self._is_fault_tolerant = is_fault_tolerant
        self._already_closed = False
        self._terminated = False

        self._seed_instance_manager()

    @property
    def is_terminated(self):
        return self._terminated

    def reset(self, episode_uid: str, agent_xmls: List[etree.Element]):
        # seed the manager
        self._seed_instance_manager()

        # Start missing instances, quit episodes, and make socket connections
        self._setup_instances()
        self._terminated = False

        # Start the Mission/Task by sending the master mission XML over
        # the pipe to these instances, and  update the agent xmls to get
        # the port/ip of the master agent send the remaining XMLS.
        self._send_mission(
            self._instances[0], agent_xmls[0], self._get_token(0, episode_uid)
        )  # Master
        if self._agent_count > 1:
            raise ValueError("TODO")

        return self._query_first_obs()

    def step(self, action_xmls: List[str]):
        """
        Bridge the MC java client step.

        Args:
            action_xmls: A list of prepared action XMLs.
        """
        assert len(action_xmls) == len(
            self._instances
        ), f"Expect {len(self._instances)} action XMLs, received {len(action_xmls)} instead"
        if not self._terminated:
            assert self.STEP_OPTIONS in {0, 2}
            all_obs = {}
            any_done = False
            for i, instance in enumerate(self._instances):
                try:
                    malmo_command = action_xmls[i]
                    step_message = f"<StepClient{str(self.STEP_OPTIONS)}>{malmo_command}</StepClient{str(self.STEP_OPTIONS)} >"
                    # Send Actions.
                    instance.client_socket_send_message(step_message.encode())
                    # Receive the (image) observation.
                    obs = instance.client_socket_recv_message()
                    # Receive reward (useless though), done, and sent.
                    reply = instance.client_socket_recv_message()
                    _, done, sent = struct.unpack("!dbb", reply)
                    any_done = any_done or (done == 1)
                    # Receive info from the environment.
                    malmo_json = instance.client_socket_recv_message().decode("utf-8")
                    raw = json.loads(malmo_json) if malmo_json is not None else {}
                    raw["pov"] = obs
                    all_obs[i] = raw
                except (socket.timeout, socket.error, TypeError) as e:
                    # when the socket times out...
                    self._terminated = True
                    logger.error(f"Failed to take a step. Error msg: {e}")
                    return StepTuple(step_success=False, raw_obs=None)
            self._terminated = any_done

            # step the server
            # instance[0] is the server
            server = self._instances[0]
            step_message = "<StepServer></StepServer>"
            try:
                server.client_socket_send_message(step_message.encode())
            except (socket.timeout, socket.error, TypeError) as e:
                self._terminated = True
                logger.error("Failed to take a step (timeout or error).")
        else:
            raise RuntimeError("Attempted to step an environment server with done=True")
        return StepTuple(step_success=True, raw_obs=all_obs)

    def close(self):
        logger.debug("Closing...")
        if self._already_closed:
            return
        for instance in self._instances:
            self._clean_connection(instance)
            if instance.running:
                instance.kill()
        self._already_closed = True

    def _setup_instances(self):
        """
        Set up MC instances
        """
        n_instances_to_start = self._agent_count - len(self._instances)
        if n_instances_to_start > 0:
            instance_futures = []
            with ThreadPoolExecutor(max_workers=n_instances_to_start) as tpe:
                for _ in range(n_instances_to_start):
                    instance_futures.append(tpe.submit(self._get_new_instance))
            self._instances.extend([f.result() for f in instance_futures])

        # establish socket connections
        for instance in reversed(self._instances):
            self._clean_connection(instance)
            self._create_connection(instance)
            # TODO: Properly rewrite fault tolerance.
            self._quit_current_episode(instance)

    def _get_new_instance(self, port=None, instance_id=None) -> MinecraftInstance:
        """
        Gets a new instance and sets up a logger if need be.
        """
        if port is not None:
            instance = InstanceManager.add_existing_instance(port)
        else:
            instance = InstanceManager.get_instance(
                os.getpid(), instance_id=instance_id
            )

        instance.launch(replaceable=self._is_fault_tolerant)
        instance.had_to_clean = False
        return instance

    def _query_first_obs(self):
        all_obs = {}
        if not self._terminated:
            logger.debug("Query the first obs.")
            peek_message = "<Peek/>"
            any_done = False
            for i, instance in enumerate(self._instances):
                st_time = time.time()
                instance.client_socket_send_message(peek_message.encode())
                obs = instance.client_socket_recv_message()
                info = instance.client_socket_recv_message().decode("utf-8")

                reply = instance.client_socket_recv_message()
                (done,) = struct.unpack("!b", reply)
                any_done = any_done or (done == 1)
                if obs is None or len(obs) == 0:
                    if time.time() - st_time > MAX_WAIT:
                        instance.client_socket_close()
                        raise Exception("too long waiting for first observation")
                    time.sleep(0.1)
                    # FIXME - shouldn't we error or retry here?

                raw = json.loads(info) if info is not None else {}
                raw["pov"] = obs
                all_obs[i] = raw
            self._terminated = any_done
            if self._terminated:
                raise RuntimeError(
                    "Something went wrong resetting the environment! "
                    "`done` was true on first frame."
                )
        return all_obs

    @retry
    def _create_connection(self, instance: MinecraftInstance):
        try:
            logger.debug(f"Creating socket connection {instance}")
            instance.create_instance_socket(socktime=self.SOCKTIME)
            logger.debug(f"Saying hello for client: {instance}")
            self._hello_server(instance)
        except (socket.timeout, socket.error, ConnectionRefusedError) as e:
            instance.had_to_clean = True
            logger.error("Failed to reset (socket error), trying again!")
            logger.error("Cleaning connection! Something must have gone wrong.")
            self._clean_connection(instance)
            self._kill_frozen_instance(instance)
            raise e

    def _seed_instance_manager(self):
        InstanceManager.seed_manager(self._rng.integers(low=0, high=2**31 - 1))

    @staticmethod
    def _send_mission(
        instance: MinecraftInstance,
        mission_xml_etree: etree.Element,
        token_in: str,
        agent_count: int = 1,
        seed: Optional[int] = None,
    ):
        """
        Send the mission XML to the given isntance.
        """
        # init all instance missions
        ok = 0
        st_time = time.time()
        logger.debug(f"Sending mission init: {instance}")
        while ok != 1:
            # roundtrip through etree to escape symbols correctly and make printing pretty
            mission_xml = etree.tostring(mission_xml_etree)
            token = f"{token_in}:{str(agent_count)}:true"
            if seed is not None:
                token += f":{seed}"
            token = token.encode()
            instance.client_socket_send_message(mission_xml)
            instance.client_socket_send_message(token)

            reply = instance.client_socket_recv_message()
            (ok,) = struct.unpack("!I", reply)
            if ok != 1:
                if (time.time() - st_time) > MAX_WAIT:
                    raise socket.timeout()
                logger.debug(f"Recieved a MALMOBUSY from {instance}; trying again.")
                time.sleep(1)

    @staticmethod
    def _clean_connection(instance: MinecraftInstance):
        """
        Clean the connection given an instance.
        No effects at the first time.
        """
        try:
            if instance.has_client_socket():
                # Try to disconnect gracefully.
                try:
                    instance.client_socket_send_message("<Disconnect/>".encode())
                except:
                    pass
                instance.client_socket_shutdown(socket.SHUT_RDWR)
        except (BrokenPipeError, OSError, socket.error):
            # There is no connection left!
            instance.client_socket = None

    @staticmethod
    def _hello_server(instance: MinecraftInstance):
        instance.client_socket_send_message(
            ("<MalmoEnv" + MALMO_VERSION + "/>").encode()
        )

    @staticmethod
    def _kill_frozen_instance(instance: MinecraftInstance):
        if instance.had_to_clean:
            logger.error(
                f"Connection with Minecraft client {instance} cleaned more than once; restarting."
            )

            instance.kill()
        else:
            instance.had_to_clean = True

    @staticmethod
    def _quit_current_episode(instance: MinecraftInstance):
        has_quit = False

        logger.info(f"Attempting to quit: {instance}")
        # while not has_quit:
        instance.client_socket_send_message("<Quit/>".encode())
        reply = instance.client_socket_recv_message()
        (ok,) = struct.unpack("!I", reply)
        has_quit = not (ok == 0)
        # TODO: Get this to work properly

        # time.sleep(0.1)

    @staticmethod
    def _get_token(role: int, ep_uid: str):
        return f"{ep_uid}:{str(role)}:0"
