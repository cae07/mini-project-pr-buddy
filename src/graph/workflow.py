from langgraph.graph import StateGraph
from langgraph.graph import END

from graph.state import PRReviewState

from graph.nodes import (
    load_diff,
    validate_input,
    security_guard,
    route_security,
    load_history,
    save_history,
    analyze_security,
    analyze_quality,
    merge_analysis,
    approve_flow,
    attention_flow,
    block_flow,
    route_recommendation,
    generate_report,
    send_notification
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
        "security_guard",
        security_guard
    )

    graph.add_node(
        "load_history",
        load_history
    )

    graph.add_node(
        "analyze_security",
        analyze_security
    )

    graph.add_node(
        "analyze_quality",
        analyze_quality
    )

    graph.add_node(
        "merge_analysis",
        merge_analysis
    )

    graph.add_node(
        "approve",
        approve_flow
    )

    graph.add_node(
        "attention",
        attention_flow
    )

    graph.add_node(
        "block",
        block_flow
    )

    graph.add_node(
        "generate_report",
        generate_report
    )

    graph.add_node(
        "save_history",
        save_history
    )

    graph.add_node(
        "send_notification",
        send_notification
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
        "security_guard"
    )

    graph.add_conditional_edges(
        "security_guard",
        route_security,
        {
            "safe": "load_history",
            "blocked": "block"
        }
    )

    #
    # Paralelização
    #

    graph.add_edge(
        "load_history",
        "analyze_security"
    )

    graph.add_edge(
        "load_history",
        "analyze_quality"
    )

    #
    # Convergência
    #

    graph.add_edge(
        "analyze_security",
        "merge_analysis"
    )

    graph.add_edge(
        "analyze_quality",
        "merge_analysis"
    )

    #
    # Ramificação condicional
    #

    graph.add_conditional_edges(
        "merge_analysis",
        route_recommendation,
        {
            "approve": "approve",
            "attention": "attention",
            "block": "block"
        }
    )

    graph.add_edge(
        "approve",
        "generate_report"
    )

    graph.add_edge(
        "attention",
        "generate_report"
    )

    graph.add_edge(
        "block",
        "generate_report"
    )

    graph.add_edge(
        "generate_report",
        "save_history"
    )

    graph.add_edge(
        "save_history",
        "send_notification"
    )

    graph.add_edge(
        "send_notification",
        END
    )

    return graph.compile()