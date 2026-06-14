from .. import base_tools
def get_tools():
    return [base_tools.query_graph, {"type" : "web_search"}]