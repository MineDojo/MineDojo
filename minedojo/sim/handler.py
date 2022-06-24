# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
from abc import ABC, abstractmethod

import jinja2


class Handler(ABC):
    """Defines the minimal interface for a MineRL handler.

    At their core, handlers should specify unique identifiers
    and a method for producing XML to be given in a mission XML.
    """

    @abstractmethod
    def to_string(self) -> str:
        """The unique identifier for the agent handler.
        This is used for constructing action/observation spaces
        and unioning different env specifications.
        """
        raise NotImplementedError()

    # @abstractmethod #TODO: This should be abstract per convention
    # but this strict handler -> xml enforcement will happen
    # with a pyxb update.
    def xml_template(self) -> str:
        """Generates an XML representation of the handler.

        This XML representation is templated via Jinja2 and
        has access to all of the member variables of the class.

        Note: This is not an abstract method so that
        handlers without corresponding XML's can be combined in
        handler groups with group based XML implementations.
        """
        raise NotImplementedError()

    def xml(self) -> str:
        """Gets the XML representation of Handler by templating
        according to the xml_template class.


        Returns:
            str: the XML representation of the handler.
        """
        var_dict = {}
        for attr_name in dir(self):
            if "xml" not in attr_name:
                var_dict[attr_name] = getattr(self, attr_name)
        try:
            env = jinja2.Environment(undefined=jinja2.StrictUndefined)
            template = env.from_string(self.xml_template())
            return template.render(var_dict)
        except jinja2.UndefinedError as e:
            # print the exception with traceback
            message = e.message + f"\nOccurred in {self}"
            raise jinja2.UndefinedError(message=message)
            pass

    def __or__(self, other):
        """
        Checks to see if self and other have the same to_string
        and if so returns self, otherwise raises an exception.
        """
        assert (
            self.to_string() == other.to_string()
        ), f"Incompatible handlers: {self} and {other}"
        return self

    def __eq__(self, other):
        """
        Checks to see if self and other have the same to_string
        and if so returns self, otherwise raises an exception.
        """
        return self.to_string() == other.to_string()

    def __repr__(self):
        return super().__repr__() + ":" + self.to_string()
