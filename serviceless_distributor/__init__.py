import pickle
import socket
from concurrent.futures import ThreadPoolExecutor

import requests
import djangoless_signing as signing


class NoSerializer:
    """Django signing uses json by default but since we need to sign bytes we can use this as serializer"""

    loads = dumps = lambda _, data: data


class StaticProperties(type):
    """To update executer according to simultaneous_requests"""

    @property
    def simultaneous_requests(self):
        return self._simultaneous_requests

    @simultaneous_requests.setter
    def simultaneous_requests(self, value):
        self._executer = ThreadPoolExecutor(max_workers=self._simultaneous_requests)
        self._simultaneous_requests = value


class Distributor(metaclass=StaticProperties):
    """
    Main class to register and do other stuffs with functions.


    Attributes
    ----------
    Distributor.config : dict
        The dictionary where all registered functions kept
    Distributor.path : str
        The path to concatenate with node addresses
    Distributor.headers : dict
        Headers to use while sending data
    Distributor.nodes : list
        Nodes IPs with protocol (Do not use load balancer IP, we couldn't know
        if all nodes affected if you use load balancer IP)
        Example: ["http://10.0.0.0", "http://10.0.0.1"]
    Distributor.key : bytes
        Key to sign your data
    Distributor.bounce_mode : bool
        if Distributor.bounce_mode == False:
            Current node sends data to all other nodes
        else:
            All nodes will send data to next node so all nodes will make only
            one request instead of len(SERVICELESS_DISTRIBUTOR_NODES)
    Distributor.simultaneous_requests : int
        Maximum number of threads to create and send requests simultaneously

    Methods
    -------
    Distributor.register_function(function,
                                  nodes=settings.SERVICELESS_DISTRIBUTOR_NODES,
                                  path="serviceless_distributor"):
        Returns new function which calls old one and distributes to other nodes
    """

    config = {}
    path = "serviceless_distributor"
    headers = {}
    nodes = []
    key = b""
    bounce_mode = True

    _simultaneous_requests = 10
    _executer = ThreadPoolExecutor(max_workers=_simultaneous_requests)
    _hostnames = socket.gethostbyname_ex(socket.gethostname())[-1]

    @staticmethod
    def register_function(nodes: list = Distributor.nodes):
        """
        Parameters
        ----------
        nodes : list, optional
            Nodes to distribute
        """

        def decorator(function):
            def distributed_function(*args, **kwargs):
                Distributor._distribute(
                    f"{function.__module__}.{function.__name__}", args, kwargs
                )
                return function(*args, **kwargs)

            for index, node in enumerate(nodes):
                if any(host in node for host in Distributor._hostnames):
                    current_node_index = index
                    break

            Distributor.config[f"{function.__module__}.{function.__name__}"] = {
                "FUNCTION": function,
                "NODES": nodes,
                "CURRENT_NODE_INDEX": current_node_index,
            }
            return distributed_function

        return decorator

    @staticmethod
    def _run_function(packed_data):
        try:
            unpacked_data = pickle.loads(
                signing.loads(packed_data, Distributor.key, serializer=NoSerializer)
            )
        except signing.BadSignature:
            return

        function_config = Distributor.config.get(unpacked_data["FUNCTION_NAME"])
        function_config["FUNCTION"](*unpacked_data["ARGS"], **unpacked_data["KWARGS"])

        nodes = Distributor._get_next_nodes(False, function_config)
        Distributor._executer.submit(Distributor._send_request, packed_data, nodes)

    @staticmethod
    def _send_request(packed_data, nodes):
        for node in nodes:
            try:
                assert (
                    200
                    == requests.post(
                        f"{node}/{Distributor.path}",
                        data={"data": packed_data},
                        headers=Distributor.headers,
                    ).status_code
                )
                if Distributor.bounce_mode:
                    break
            except:
                if Distributor.bounce_mode:
                    Distributor._executer.submit(
                        Distributor._send_request, packed_data, nodes[1:]
                    )

    @staticmethod
    def _get_next_nodes(is_distribution, function_config):
        if is_distribution:
            nodes = function_config["NODES"][:]
            del nodes[function_config["CURRENT_NODE_INDEX"]]
        else:
            if Distributor.bounce_mode:
                nodes = function_config["NODES"][
                    function_config["CURRENT_NODE_INDEX"] + 1 :
                ]
            else:
                nodes = []
        return nodes

    @staticmethod
    def _distribute(full_function_name, args, kwargs):
        packed_data = signing.dumps(
            pickle.dumps(
                {"FUNCTION_NAME": full_function_name, "ARGS": args, "KWARGS": kwargs}
            ),
            Distributor.key,
            serializer=NoSerializer,
        )

        function_config = Distributor.config[full_function_name]
        nodes = Distributor._get_next_nodes(True, function_config)

        Distributor._executer.submit(Distributor._send_request, packed_data, nodes)
