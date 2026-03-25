from agent_deployment_readiness_lab.graph import build_graph


def test_graph_builds():
    graph = build_graph()
    assert hasattr(graph, "invoke")

