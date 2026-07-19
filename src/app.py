from graph.workflow import build_graph
from dotenv import load_dotenv

load_dotenv()

graph = build_graph()

result = graph.invoke({
    "file_path": "examples/diff.txt"
})

print()
print("RESUMO")
print(result["summary"])

print()
print("RECOMENDACAO")
print(result["recommendation"])

print()
print("RELATORIO")
print(result["report_path"])