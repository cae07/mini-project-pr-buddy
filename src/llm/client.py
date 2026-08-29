import json
import os


class LLMClient:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "google").lower()
        self.timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

        if self.provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError as exc:
                raise RuntimeError("langchain_google_genai is required for provider 'google'.") from exc

            self.client = ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "GEMINI_MODEL"),
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0,
                request_timeout=self.timeout,
            )

        elif self.provider == "groq":
            try:
                from langchain_groq import ChatGroq
            except ImportError as exc:
                raise RuntimeError("langchain_groq is required for provider 'groq'. Install with 'pip install langchain-groq'.") from exc

            self.client = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model=os.getenv("GROQ_MODEL", "groq-alpha"))

        elif self.provider == "mcp":
            self.mcp_url = os.getenv("MCP_URL")
            if not self.mcp_url:
                raise RuntimeError("MCP_URL must be set when LLM_PROVIDER=mcp")
            try:
                import requests
            except (
                TimeoutError,
                ValueError,
                requests.RequestException,
            ) as exc:
                raise RuntimeError("requests library is required for MCP provider. Install with 'pip install requests'.") from exc
            self.requests = requests

        else:
            raise RuntimeError(f"Unknown LLM_PROVIDER '{self.provider}'")

    def invoke(self, prompt, config=None):
        config = config or {}

        if self.provider == "mcp":
            resp = self.requests.post(self.mcp_url, json={"prompt": prompt, "config": config}, timeout=self.timeout)
            resp.raise_for_status()
            try:
                body = resp.json()
            except ValueError:
                body = {"content": resp.text}

            content = body.get("content") or body.get("response") or body.get("result") or body.get("output") or body.get("text")
            if content is None:
                content = json.dumps(body, ensure_ascii=False)

            class Response:
                pass

            r = Response()
            r.content = content
            r.usage_metadata = body.get("usage", {}) if isinstance(body, dict) else {}
            return r

        # Delegation for provider clients (google / groq)
        client = getattr(self, "client", None)
        if client is None:
            raise RuntimeError("LLM client not initialized")

        # Prefer an invoke method if available
        if hasattr(client, "invoke"):
            return client.invoke(prompt, config=config)

        # Fallbacks for other client shapes
        if hasattr(client, "chat"):
            return client.chat(prompt)

        # Last resort, call the object
        return client(prompt)
