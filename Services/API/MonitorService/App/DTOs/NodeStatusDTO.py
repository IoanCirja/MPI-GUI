class NodeStatusDTO:
    def __init__(self, node_name: str, status: bool):
        self.node_name = node_name
        self.status = status
