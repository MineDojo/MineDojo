import os
from typing import List, Optional

import jinja2
from lxml import etree

from . import spaces as spaces
from .handler import Handler
from .handlers.translation import TranslationHandler
from .bridge.mc_instance.instance import MALMO_VERSION


MISSION_TEMPLATE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "mc_meta", "minedojo_mission.xml.j2"
)


class SimSpec:
    MALMO_VERSION = MALMO_VERSION

    def __init__(
        self,
        *,
        sim_name: str,
        agent_count: int = 1,
        obs_handlers: List[TranslationHandler],
        action_handlers: List[TranslationHandler],
        agent_handlers: List[Handler],
        agent_start_handlers: List[Handler],
        server_initial_conditions_handlers: List[Handler],
        world_generator_handlers: List[Handler],
        server_decorator_handlers: List[Handler],
        server_quit_handlers: List[Handler],
        seed: Optional[int] = None,
    ):
        self._sim_name = sim_name
        assert agent_count == 1, "TODO"
        self._agent_count = agent_count
        self._agent_names = [f"agent_{role}" for role in range(agent_count)]

        self._obs_handlers = obs_handlers
        self._action_handlers = action_handlers
        self._agent_handlers = agent_handlers
        self._server_initial_conditions_handlers = server_initial_conditions_handlers
        self._world_generator_handlers = world_generator_handlers
        self._server_decorator_handlers = server_decorator_handlers
        self._server_quit_handlers = server_quit_handlers
        self._agent_start_handlers_list = [
            agent_start_handlers for _ in range(agent_count)
        ]

        # check that the obs/action have no duplicate to_strings
        assert len([o.to_string() for o in self._obs_handlers]) == len(
            set([o.to_string() for o in self._obs_handlers])
        )
        assert len([a.to_string() for a in self._action_handlers]) == len(
            set([a.to_string() for a in self._action_handlers])
        )
        self._observation_space = self.create_observation_space()
        self._action_space = self.create_action_space()
        self._observation_space.seed(seed)
        self._action_space.seed(seed)

        self._episode_id = None

    @property
    def observation_space(self) -> spaces.Dict:
        return self._observation_space

    @property
    def action_space(self) -> spaces.Dict:
        return self._action_space

    @property
    def observables(self):
        return self._obs_handlers

    @property
    def actionables(self):
        return self._action_handlers

    def _singlify(self, space: spaces.Dict):
        if self._agent_count == 1:
            return space.spaces[self._agent_names[0]]
        else:
            return space

    def create_observation_space(self):
        return self._singlify(
            spaces.Dict(
                {
                    agent: spaces.Dict(
                        {o.to_string(): o.space for o in self._obs_handlers}
                    )
                    for agent in self._agent_names
                }
            )
        )

    def create_action_space(self):
        return self._singlify(
            spaces.Dict(
                {
                    agent: spaces.Dict(
                        {a.to_string(): a.space for a in self._action_handlers}
                    )
                    for agent in self._agent_names
                }
            )
        )

    def to_xml(self, episode_id: str) -> str:
        """
        Gets the XML by templating mission.xml.j2 using Jinja
        """
        self._episode_id = episode_id
        with open(MISSION_TEMPLATE, "rt") as fh:
            var_dict = {}
            for attr_name in dir(self):
                if "to_xml" not in attr_name:
                    var_dict[attr_name] = getattr(self, attr_name)

            env = jinja2.Environment(undefined=jinja2.StrictUndefined)
            template = env.from_string(fh.read())

        xml = template.render(var_dict)
        # Now do one more pretty printing

        xml = etree.tostring(
            etree.fromstring(xml.encode("utf-8")), pretty_print=True
        ).decode("utf-8")
        return xml

    @staticmethod
    def get_consolidated_xml(handlers: List[Handler]) -> List[str]:
        """Consolidates duplicate XML representations from the handlers.

        Deduplication happens by first getting all handler.xml() strings
        of the handlers, and then converting them into etrees. After that we check
        if there are any top level elements that are duplicated and pick the first of them
        to retain. We then convert the remaining etrees back into strings and join them with new lines.

        Args:
            handlers (List[Handler]): A list of handlers to consolidate.

        Returns:
            str: The XML
        """
        handler_xml_strs = [handler.xml() for handler in handlers]

        if not handler_xml_strs:
            return ""

        # TODO: RAISE VALID XML ERROR. FOR EASE OF USE
        trees = [etree.fromstring(xml) for xml in handler_xml_strs if xml != ""]
        consolidated_trees = {tree.tag: tree for tree in trees}.values()

        return [
            etree.tostring(t, pretty_print=True).decode("utf-8")
            for t in consolidated_trees
        ]
