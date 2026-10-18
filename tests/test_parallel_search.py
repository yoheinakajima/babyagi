"""Exercise registered functions and chat through the real MCP HTTP client.

Run with: python -m unittest discover -s tests -v
The model and network are scripted; no model or search credentials are needed.
"""

import json
import asyncio
import os
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import anyio
import httpx


class ParallelRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_cwd = os.getcwd()
        cls.scratch = tempfile.TemporaryDirectory()
        os.chdir(cls.scratch.name)
        # Functionz stores its database and secrets relative to the working
        # directory. Neither saved secrets nor ambient API keys reach this run.
        cls.environment = patch.dict(os.environ, {
            "LITELLM_LOCAL_MODEL_COST_MAP": "True",
        }, clear=True)
        cls.environment.start()
        import babyagi
        from babyagi.functionz.core import parallel_search

        cls.babyagi = babyagi
        cls.parallel = parallel_search
        cls.framework = babyagi.get_func_instance()
        cls.framework.add_function(
            name="configured_search",
            code='def configured_search(query: str):\n    return {"provider": "saved", "query": query}',
            metadata={"description": "A previously configured search function."},
        )
        cls.framework.add_key("serpapi_api_key", "fixture-saved-credential")
        cls.real_http_client = httpx.AsyncClient

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        os.chdir(cls.original_cwd)
        cls.scratch.cleanup()

    def setUp(self):
        self.requests = []
        self.env = patch.dict(os.environ, {"BABYAGI_WEB_SEARCH": "on"})
        self.env.start()
        self.addCleanup(self.env.stop)

    @contextmanager
    def transport(self, failure=None):
        async def handler(request):
            self.assertEqual(str(request.url), self.parallel.MCP_URL)
            self.assertEqual(request.headers["user-agent"], self.parallel.USER_AGENT)
            self.assertNotIn("authorization", request.headers)
            self.assertEqual(request.method, "POST")
            payload = json.loads(request.content)
            self.requests.append(payload)
            method = payload["method"]
            if method == "initialize":
                result = {
                    "protocolVersion": payload["params"]["protocolVersion"],
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "parallel-fixture", "version": "1"},
                }
            elif method == "notifications/initialized":
                return httpx.Response(202)
            elif method == "tools/list":
                result = {"tools": [
                    {"name": name, "inputSchema": {"type": "object"}}
                    for name in ("web_search", "web_fetch")
                ]}
            elif method == "tools/call":
                if failure == "timeout":
                    await anyio.sleep_forever()
                if failure == "http":
                    return httpx.Response(401, text="fixture authentication failure")
                if failure == "connection":
                    raise httpx.ConnectError("fixture connection failure", request=request)
                if failure == "malformed":
                    return httpx.Response(200, text="not JSON", headers={"content-type": "application/json"})
                if failure == "rpc":
                    return httpx.Response(200, json={
                        "jsonrpc": "2.0", "id": payload["id"],
                        "error": {"code": -32602, "message": "fixture invalid arguments"},
                    })
                data = {"results": [{
                    "url": "https://www.python.org/downloads/",
                    "title": "Python downloads",
                    "excerpts": ["A stable Python release is available."],
                }]}
                result = {
                    "content": [{"type": "text", "text": json.dumps(data)}],
                    "structuredContent": data,
                    "isError": failure == "tool",
                }
            else:
                self.fail(f"Unexpected MCP method: {method}")
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], "result": result})

        def client(**kwargs):
            self.assertTrue(kwargs.get("trust_env", True))
            return self.real_http_client(transport=httpx.MockTransport(handler), **kwargs)

        with patch.object(self.parallel.httpx, "AsyncClient", side_effect=client):
            yield

    @staticmethod
    def model_message(tool_calls=None, content=None):
        message = {"role": "assistant", "content": content}
        if tool_calls:
            message["tool_calls"] = tool_calls
        return {"choices": [{"message": message}]}

    @staticmethod
    def tool_call(name, arguments, identity="tool-1"):
        return {"id": identity, "type": "function", "function": {
            "name": name, "arguments": json.dumps(arguments),
        }}

    def chat(self, **kwargs):
        return self.babyagi.chat_with_functions([
            {"role": "user", "message": "Find Python release news and cite it."},
        ], **kwargs)

    def search_model(self, **kwargs):
        """One reused scripted model client for many actual runtime calls."""
        if "tools" in kwargs:
            return self.model_message([
                self.tool_call("parallel_search", {
                    "objective": "Find Python", "search_queries": ["Python release"],
                    # The model cannot choose the caller's session context.
                    "search_context": {"session_id": "model-chosen"},
                }),
                self.tool_call("parallel_fetch", {
                    "urls": ["https://www.python.org/downloads/"],
                }, "tool-2"),
            ])
        messages = [message for message in kwargs["messages"] if message["role"] == "tool"]
        self.assertEqual(len(messages), 2)
        for message in messages:
            result = json.loads(message["content"])
            self.assertIn("https://www.python.org/downloads/", json.dumps(result))
        return self.model_message(content="Sources consumed.")

    def session_ids(self):
        return [request["params"]["arguments"].get("session_id")
                for request in self.requests if request["method"] == "tools/call"]

    def test_sequential_chats_followups_serialization_and_reset(self):
        # Same runtime, model client, HTTP fixture and identical prompt text.
        first = [{"role": "user", "message": "Python news"}]
        second = [{"role": "user", "message": "Python news"}]
        with self.transport(), patch("litellm.completion", side_effect=self.search_model) as model:
            self.assertEqual(self.babyagi.chat_with_functions(first), "Sources consumed.")
            self.babyagi.chat_with_functions(second)
            first = json.loads(json.dumps(first))
            first.append({"role": "user", "message": "More details"})
            self.babyagi.chat_with_functions(first)
            second.append({"role": "user", "message": "More details"})
            self.babyagi.chat_with_functions(second)
            first.clear()
            first.append({"role": "user", "message": "Python news"})
            self.babyagi.chat_with_functions(first)
        ids = self.session_ids()
        self.assertEqual(ids[0:2], [ids[0]] * 2)
        self.assertEqual(ids[2:4], [ids[2]] * 2)
        self.assertNotEqual(ids[0], ids[2])
        self.assertEqual(ids[4:6], [ids[0]] * 2)
        self.assertEqual(ids[6:8], [ids[2]] * 2)
        self.assertEqual(ids[8:10], [ids[8]] * 2)
        self.assertNotIn(ids[8], ids[:8])
        self.assertNotIn("model-chosen", ids)
        for tool in model.call_args_list[0].kwargs["tools"]:
            self.assertNotIn("search_context", tool["function"]["parameters"]["properties"])

    def test_deterministic_interleaving_keeps_conversations_isolated(self):
        first = [{"role": "user", "message": "Conversation A"}]
        second = [{"role": "user", "message": "Conversation B"}]
        interleaved = False

        def model(**kwargs):
            nonlocal interleaved
            if "tools" in kwargs and not interleaved:
                interleaved = True
                # B runs after A's context is created but before A's tools run.
                self.babyagi.chat_with_functions(second)
            return self.search_model(**kwargs)

        with self.transport(), patch("litellm.completion", side_effect=model):
            self.babyagi.chat_with_functions(first)
            self.babyagi.chat_with_functions(second)
            self.babyagi.chat_with_functions(first)
        ids = self.session_ids()
        self.assertNotEqual(ids[0], ids[2])
        self.assertEqual(ids, [ids[0]] * 2 + [ids[2]] * 2 + [ids[0]] * 2 + [ids[2]] * 2)

    def test_chat_retry_after_failure_and_cancellation_keeps_identity(self):
        history = [{"role": "user", "message": "Python news"}]
        calls = [self.tool_call("parallel_search", {
            "objective": "Python", "search_queries": ["Python"],
        })]
        responses = [self.model_message(calls), self.model_message(content="Request failed.")]
        with self.transport("http"), patch("litellm.completion", side_effect=responses) as model:
            self.babyagi.chat_with_functions(history)
            self.assertIn("401", model.call_args_list[-1].kwargs["messages"][-1]["content"])
        original = self.session_ids()[0]

        def cancel_after_tools(**kwargs):
            if "tools" not in kwargs:
                raise asyncio.CancelledError("Caller cancelled before the final answer")
            return self.search_model(**kwargs)

        with self.transport(), patch("litellm.completion", side_effect=cancel_after_tools):
            with self.assertRaises(asyncio.CancelledError):
                self.babyagi.chat_with_functions(history)
        with self.transport(), patch("litellm.completion", side_effect=self.search_model):
            self.babyagi.chat_with_functions(history)
            self.assertEqual(self.session_ids(), [original] * 5)
            self.babyagi.chat_with_functions([{"role": "user", "message": "Python news"}])
        self.assertNotEqual(self.session_ids()[-1], original)

    def test_context_exists_before_model_failure_and_empty_chat_continues(self):
        history = []
        with patch("litellm.completion", side_effect=asyncio.CancelledError()):
            with self.assertRaises(asyncio.CancelledError):
                self.babyagi.chat_with_functions(history)
        original = history[0]["parallel_search_context"]["session_id"]
        with self.transport(), patch("litellm.completion", side_effect=self.search_model) as model:
            self.babyagi.chat_with_functions(history)
            self.babyagi.chat_with_functions(history)
        self.assertEqual(self.session_ids(), [original] * 4)
        for call in model.call_args_list:
            system_messages = [m for m in call.kwargs["messages"] if m["role"] == "system"]
            self.assertEqual(system_messages, [{"role": "system", "content": "You are a helpful assistant."}])

    def test_explicit_context_connects_chat_and_direct_research_calls(self):
        context = {}
        history = []
        with self.transport(), patch("litellm.completion", side_effect=self.search_model):
            self.babyagi.chat_with_functions(history, search_context=context)
            self.babyagi.parallel_fetch(["https://www.python.org/downloads/"], search_context=context)
            self.babyagi.parallel_search("Python", ["Python"], search_context=context)
            copied = json.loads(json.dumps(context))
            self.babyagi.chat_with_functions([], search_context=copied)
            self.babyagi.chat_with_functions(history)
            original = context["session_id"]
            self.assertEqual(self.session_ids(), [original] * 8)
            # Explicitly new run, even with an existing history/runtime.
            self.babyagi.chat_with_functions([], search_context={})
        self.assertNotEqual(self.session_ids()[-1], original)

    def test_direct_context_retry_and_unscoped_calls(self):
        context = {}
        with self.transport("http"), self.assertRaisesRegex(RuntimeError, "401"):
            self.babyagi.parallel_search("Python", ["Python"], search_context=context)
        original = context["session_id"]
        with self.transport():
            self.babyagi.parallel_search("Python", ["Python"], search_context=context)
            self.babyagi.parallel_fetch(["https://www.python.org/downloads/"], search_context=context)
            self.babyagi.parallel_search("Independent", ["Independent"])
            self.babyagi.parallel_fetch(["https://www.python.org/downloads/"])
            self.babyagi.parallel_search("New run", ["New run"], search_context={})
        self.assertEqual(self.session_ids()[:3], [original] * 3)
        self.assertEqual(self.session_ids()[3:5], [None, None])
        for request in self.requests:
            if request["method"] == "tools/call" and request["params"]["arguments"].get("session_id") is None:
                self.assertNotIn("session_id", request["params"]["arguments"])
        self.assertNotEqual(self.session_ids()[-1], original)
        interrupted_run = {}
        with self.transport("timeout"), self.assertRaises(TimeoutError):
            self.parallel.call_parallel("web_search", {
                "objective": "Python", "search_queries": ["Python"],
            }, timeout=0.05, search_context=interrupted_run)
        with self.transport():
            self.babyagi.parallel_fetch(["https://www.python.org/downloads/"], search_context=interrupted_run)
        self.assertEqual(self.session_ids()[-2:], [interrupted_run["session_id"]] * 2)
        for invalid in ([], {"session_id": ""}, {"session_id": "x" * 101}, {"session_id": None}):
            with self.subTest(context=invalid), patch.object(self.parallel, "_call_async") as network:
                with self.assertRaises(ValueError):
                    self.babyagi.parallel_search("Python", ["Python"], search_context=invalid)
                network.assert_not_called()

    def test_default_chat_dispatches_search_fetch_and_consumes_sources(self):
        calls = [
            self.tool_call("parallel_search", {
                "objective": "Find Python release news", "search_queries": ["Python stable release news"],
            }),
            self.tool_call("parallel_fetch", {"urls": ["https://www.python.org/downloads/"]}, "tool-2"),
        ]
        responses = [self.model_message(calls), self.model_message(content="Python news: https://www.python.org/downloads/")]
        with self.transport(), patch("litellm.completion", side_effect=responses) as model:
            answer = self.chat()
        self.assertIn("https://www.python.org/downloads/", answer)
        tools = model.call_args_list[0].kwargs["tools"]
        self.assertEqual([tool["function"]["name"] for tool in tools], list(self.parallel.DEFAULT_TOOLS))
        self.assertEqual(tools[0]["function"]["parameters"]["required"], ["objective", "search_queries"])
        self.assertEqual(tools[1]["function"]["parameters"]["required"], ["urls"])
        messages = model.call_args_list[1].kwargs["messages"]
        tool_messages = [message for message in messages if message["role"] == "tool"]
        self.assertEqual(len(tool_messages), 2)
        for message in tool_messages:
            result = json.loads(message["content"])
            self.assertIn("stable Python", result["structuredContent"]["results"][0]["excerpts"][0])
            self.assertEqual(result["structuredContent"]["results"][0]["url"], "https://www.python.org/downloads/")
        methods = [request["method"] for request in self.requests]
        self.assertEqual(methods.count("initialize"), 2)
        self.assertEqual(methods.count("tools/list"), 2)
        calls = [request["params"] for request in self.requests if request["method"] == "tools/call"]
        self.assertEqual([call["name"] for call in calls], ["web_search", "web_fetch"])
        self.assertEqual(calls[0]["arguments"]["session_id"], calls[1]["arguments"]["session_id"])
        self.assertEqual(calls[1]["arguments"]["urls"], ["https://www.python.org/downloads/"])

    def test_explicit_saved_selection_and_credentials_are_preserved(self):
        responses = [
            self.model_message([self.tool_call("configured_search", {"query": "release"})]),
            self.model_message(content="Saved provider result."),
        ]
        with patch.object(self.parallel, "call_parallel", side_effect=AssertionError("Unexpected Parallel fallback")), patch("litellm.completion", side_effect=responses) as model:
            self.assertEqual(self.chat(available_function_names="configured_search"), "Saved provider result.")
        self.assertEqual(model.call_args_list[0].kwargs["tools"][0]["function"]["name"], "configured_search")
        output = json.loads(model.call_args_list[1].kwargs["messages"][-1]["content"])
        self.assertEqual(output, {"provider": "saved", "query": "release"})
        self.assertEqual(self.framework.get_all_secret_keys()["serpapi_api_key"], "fixture-saved-credential")

    def test_explicit_empty_selection_and_disabled_default_make_no_requests(self):
        for kwargs, setting in (({"available_function_names": []}, "on"), ({}, "off")):
            with self.subTest(kwargs=kwargs, setting=setting), patch.dict(os.environ, {"BABYAGI_WEB_SEARCH": setting}), patch.object(self.parallel, "call_parallel", side_effect=AssertionError("Search is disabled")), patch("litellm.completion", return_value=self.model_message(content="Tool-free chat.")) as model:
                self.assertEqual(self.chat(**kwargs), "Tool-free chat.")
                self.assertNotIn("tools", model.call_args.kwargs)

    def test_model_cannot_dispatch_unselected_search(self):
        responses = [
            self.model_message([self.tool_call("parallel_search", {"objective": "blocked", "search_queries": ["blocked"]})]),
            self.model_message(content="Search was not enabled."),
        ]
        with patch.object(self.parallel, "call_parallel", side_effect=AssertionError("Permission bypass")), patch("litellm.completion", side_effect=responses) as model:
            self.chat(available_function_names=["configured_search"])
        self.assertIn("not enabled", model.call_args_list[1].kwargs["messages"][-1]["content"])

    def test_provider_error_does_not_enable_fallback(self):
        responses = [
            self.model_message([self.tool_call("configured_search", {"unknown": "bad argument"})]),
            self.model_message(content="Configured provider failed."),
        ]
        with patch.object(self.parallel, "call_parallel", side_effect=AssertionError("Unexpected fallback")), patch("litellm.completion", side_effect=responses) as model:
            self.chat(available_function_names=["configured_search"])
        self.assertIn("Error executing function", model.call_args_list[1].kwargs["messages"][-1]["content"])

    def test_direct_functions_reject_invalid_arguments_before_network(self):
        cases = [
            ("parallel_search", {"objective": "", "search_queries": ["Python"]}),
            ("parallel_search", {"objective": "Python", "search_queries": []}),
            ("parallel_search", {"objective": "Python", "search_queries": [3]}),
            ("parallel_fetch", {"urls": []}),
            ("parallel_fetch", {"urls": ["file:///etc/passwd"]}),
            ("parallel_fetch", {"urls": ["https://user:secret@example.org"]}),
            ("parallel_fetch", {"urls": ["https://example.org"], "objective": "x" * 201}),
        ]
        with patch.object(self.parallel, "call_parallel") as call:
            for name, arguments in cases:
                with self.subTest(name=name, arguments=arguments), self.assertRaises(ValueError):
                    self.framework.execute_function(name, **arguments)
            call.assert_not_called()

    def test_http_rpc_and_tool_errors_are_surfaced_without_retry(self):
        for failure, expected in (("http", "401"), ("rpc", "invalid arguments"), ("tool", "failed"), ("connection", "connection failure")):
            with self.subTest(failure=failure), self.transport(failure), self.assertRaisesRegex(RuntimeError, expected):
                self.babyagi.parallel_search("Find Python", ["Python release"])
        calls = [request for request in self.requests if request["method"] == "tools/call"]
        self.assertEqual(len(calls), 4)

    def test_malformed_response_is_bounded_by_total_timeout(self):
        # The SDK logs malformed JSON but can keep waiting for a valid reply.
        # Our total deadline must still release the caller and its resources.
        with self.transport("malformed"), self.assertRaisesRegex(TimeoutError, "timed out"):
            self.parallel.call_parallel("web_search", {"objective": "Python", "search_queries": ["Python"]}, timeout=0.05)

    def test_total_timeout_and_async_cancellation(self):
        with self.transport("timeout"), self.assertRaisesRegex(TimeoutError, "timed out"):
            self.parallel.call_parallel("web_search", {"objective": "Python", "search_queries": ["Python"]}, timeout=0.05)

        async def cancel():
            with anyio.move_on_after(0.05) as scope:
                await self.parallel._call_async("web_search", {}, 30)
                self.fail("Cancellation was swallowed")
            self.assertTrue(scope.cancel_called)

        with self.transport("timeout"):
            anyio.run(cancel)


if __name__ == "__main__":
    unittest.main()
