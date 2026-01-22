from dotenv import load_dotenv
from app.core.graph import app_graph
from langchain_core.messages import HumanMessage

load_dotenv()


def run_hitl_test():
    config = {"configurable": {"thread_id": "test_123"}}

    # Solo enviamos inputs si es la PRIMERA VEZ que corre este thread
    snapshot = app_graph.get_state(config)

    if not snapshot.values:
        print("\n--- 🤖 Iniciando nueva sesión ---")
        inputs = {"messages": [HumanMessage(content="Search for NVIDIA stock price and save it to nvidia.txt")],
                  "total_tokens": 0}
    else:
        print("\n--- 🔄 Recuperando sesión existente ---")
        inputs = None

    # Ejecución hasta el breakpoint
    for event in app_graph.stream(inputs, config, stream_mode="values"):
        last_msg = event["messages"][-1]
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            print(f"\n[PLAN DEL AGENTE]: {last_msg.tool_calls[0]['name']}")

    # --- VERIFICACIÓN DE PAUSA ---
    snapshot = app_graph.get_state(config)
    if snapshot.next:
        print(f"\n--- 🛑 INTERRUPCIÓN ACTIVA EN: {snapshot.next} ---")
        confirm = input("¿Autorizas la ejecución? (yes/no): ")

        if confirm.lower() == "yes":
            print("\n--- ✅ Reanudando... ---")
            # IMPORTANTE: Volvemos a llamar a stream con None para que procese el nodo pausado
            for event in app_graph.stream(None, config, stream_mode="values"):
                # Aquí imprimimos para ver qué está pasando realmente
                last_msg = event["messages"][-1]
                if last_msg.content:
                    print(f"\n[RESPUESTA]: {last_msg.content[:200]}...")

            print("\n--- ✨ Proceso completado. Revisa tu carpeta 'output' ---")
        else:
            print("\n--- ❌ Ejecución cancelada. ---")


if __name__ == "__main__":
    run_hitl_test()