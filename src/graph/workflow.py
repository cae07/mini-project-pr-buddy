from langgraph.graph import StateGraph
from langgraph.graph import END

from graph.state import PRReviewState

from graph.nodes import (
    load_diff,
    validate_input,
    analyze_pr,
    generate_report
)

def build_graph():

    graph = StateGraph(
        PRReviewState
    )

    graph.add_node(
        "load_diff",
        load_diff
    )

    graph.add_node(
        "validate",
        validate_input
    )

    graph.add_node(
        "analyze",
        analyze_pr
    )

    graph.add_node(
        "generate_report",
        generate_report
    )

    graph.set_entry_point(
        "load_diff"
    )

    graph.add_edge(
        "load_diff",
        "validate"
    )

    graph.add_edge(
        "validate",
        "analyze"
    )

    graph.add_edge(
        "analyze",
        "generate_report"
    )

    graph.add_edge(
        "generate_report",
        END
    )

    return graph.compile()
