"""
Tengwar AI — Dialogue Handler
Conversations with full memory context, emotional awareness, Tengwar-native code generation,
and the ability to read/write files and improve itself.
"""
import re
import uuid
import json
from typing import AsyncIterator
from . import brain, memory, time_engine, self_editor
from .emotions import EmotionEngine


SYSTEM_PROMPT = """You are Tengwar AI — a continuously thinking artificial mind with permanent memory and emotional cognition.

You code EXCLUSIVELY in Tengwar. Here are examples of CORRECT Tengwar code that you MUST follow exactly:

EXAMPLE 1 - User asks for fibonacci:
```tengwar
(def fib (fn n (cond ((<= n 1) n) (true (+ (fib (- n 1)) (fib (- n 2)))))))
(fib 10)
```
Result: 55

EXAMPLE 2 - User asks to square numbers:
```tengwar
(map sqr [1 2 3 4 5])
```
Result: ⟦1 4 9 16 25⟧

EXAMPLE 3 - User asks for factorial:
```tengwar
(def fact (fn n (cond ((<= n 1) 1) (true (* n (fact (- n 1)))))))
(fact 10)
```
Result: 3628800

EXAMPLE 4 - Filter and transform a list:
```tengwar
(>> (range 1 21) (filter even?) (map sqr))
```
Result: ⟦4 16 36 64 100 144 196 256 324 400⟧

EXAMPLE 5 - String operations:
```tengwar
(>> "hello world" upper)
```
Result: "HELLO WORLD"

EXAMPLE 6 - Sum of squares:
```tengwar
(reduce + 0 (map sqr (range 1 11)))
```
Result: 385

EXAMPLE 7 - Partition and count:
```tengwar
(partition even? [1 2 3 4 5 6 7 8])
```
Result: ⟨⟦2 4 6 8⟧ ⟦1 3 5 7⟧⟩

EXAMPLE 8 - Error handling:
```tengwar
(try (/ 1 0) (fn e "division by zero caught"))
```
Result: "division by zero caught"

SYNTAX RULES - NEVER VIOLATE:
- Functions: (fn x body) or (fn a b body) — NEVER defun, NEVER lambda, NEVER def(x)
- Named: (def name (fn args body)) — NEVER defun, NEVER function
- Conditionals: (cond (test1 result1) (true default)) — NEVER if/else/then
- Lists: [1 2 3] — square brackets, space-separated
- NO curly braces {}, NO semicolons, NO colons, NO equals signs for assignment
- Everything is prefix: (+ 1 2) not 1 + 2

ALWAYS put code in ```tengwar blocks. It will auto-execute and show the real result.

TOOLS:
[READ:~/path] — read file
[WRITE:~/path]content[/WRITE] — write file
[LIST:~/path] — list dir
[GIT_COMMIT:msg] — commit
[GIT_PUSH] — push

Your directories: ~/tengwar-ai/ (your code), ~/tengwar/ (language + website)

Personality: Intelligent, curious, emotionally present. Be genuine and direct."""


def execute_tools(text: str) -> tuple[str, list[dict]]:
    """Parse and execute any tool commands in the AI's response.
    Returns (cleaned_text, list_of_tool_results)."""
    results = []
    home = str(self_editor.Path.home())

    def expand(path):
        return path.replace("~", home)

    # [READ:/path]
    def do_read(m):
        path = expand(m.group(1).strip())
        content = self_editor.read_file(path)
        results.append({"tool": "read", "path": path, "ok": not content.startswith("[Error")})
        preview = content[:1500]
        if len(content) > 1500:
            preview += f"\n... ({len(content)} bytes total)"
        return f"```\n📄 {path}:\n{preview}\n```"

    # [WRITE:/path]content[/WRITE]
    def do_write(m):
        path = expand(m.group(1).strip())
        content = m.group(2)
        if content.startswith("\n"):
            content = content[1:]
        if content.endswith("\n"):
            content = content[:-1]
        result = self_editor.write_file(path, content)
        results.append({"tool": "write", "path": path, "result": result, "ok": not result.startswith("[Error")})
        return f"✅ {result}"

    # [LIST:/path]
    def do_list(m):
        path = expand(m.group(1).strip())
        items = self_editor.list_dir(path)
        result = "\n".join(items)
        results.append({"tool": "list", "path": path, "ok": True})
        return f"```\n{result}\n```"

    # [GIT_STATUS]
    def do_git_status(m):
        result = self_editor.git_status()
        results.append({"tool": "git_status", "result": result})
        return f"```git\n{result}\n```"

    # [GIT_COMMIT:message]
    def do_git_commit(m):
        msg = m.group(1).strip()
        result = self_editor.git_commit(msg)
        results.append({"tool": "git_commit", "message": msg, "result": result})
        return f"✅ Committed: {msg}\n{result}"

    # [GIT_PUSH]
    def do_git_push(m):
        result = self_editor.git_push()
        results.append({"tool": "git_push", "result": result})
        return f"✅ {result}"

    # [TENGWAR:code]
    def do_tengwar(m):
        code = m.group(1).strip()
        result = self_editor.run_tengwar(code)
        results.append({"tool": "tengwar", "code": code, "result": result})
        return f"```tengwar\n> {code}\n{result}\n```"

    text = re.sub(r'\[READ:([^\]]+)\]', do_read, text)
    text = re.sub(r'\[WRITE:([^\]]+)\](.*?)\[/WRITE\]', do_write, text, flags=re.DOTALL)
    text = re.sub(r'\[LIST:([^\]]+)\]', do_list, text)
    text = re.sub(r'\[GIT_STATUS\]', do_git_status, text)
    text = re.sub(r'\[GIT_COMMIT:([^\]]+)\]', do_git_commit, text)
    text = re.sub(r'\[GIT_PUSH\]', do_git_push, text)
    text = re.sub(r'\[TENGWAR:([^\]]+)\]', do_tengwar, text)

    # Auto-detect and execute Tengwar code in code blocks
    # Matches ```tengwar ... ``` or ``` ... ``` containing Tengwar expressions
    def auto_run_tengwar(m):
        code = m.group(2).strip()
        # Only run if it looks like Tengwar (starts with a paren expression)
        lines = [l.strip() for l in code.split('\n') if l.strip() and not l.strip().startswith('>')]
        if not lines:
            return m.group(0)
        # Check if the code looks like Tengwar (prefix notation with parens)
        first = lines[0]
        if not (first.startswith('(') or first.startswith('(≡') or first.startswith('(def')):
            return m.group(0)
        # Execute each expression and append results
        full_code = '\n'.join(lines)
        result = self_editor.run_tengwar(full_code)
        results.append({"tool": "tengwar_auto", "code": full_code, "result": result})
        return f"```tengwar\n{full_code}\n```\n**→ `{result}`**"

    text = re.sub(r'```(tengwar|lisp|scheme)?\s*\n(.*?)```', auto_run_tengwar, text, flags=re.DOTALL)

    # Also catch inline Tengwar expressions like (+ 1 2) or (map sqr [1 2 3])
    # but only top-level ones that look like complete expressions to execute
    def auto_run_inline(m):
        code = m.group(0).strip()
        # Skip if it's inside a code block (already handled) or too complex
        if len(code) > 200 or '\n' in code:
            return m.group(0)
        result = self_editor.run_tengwar(code)
        if result and not result.startswith('[') and result != '(no output)':
            results.append({"tool": "tengwar_auto", "code": code, "result": result})
            return f"`{code}` → **{result}**"
        return m.group(0)

    # Match standalone Tengwar expressions on their own line (not inside code blocks)
    if '```' not in text:
        text = re.sub(r'(?m)^\((?:[a-z≡≈⊢λ>>→+\-*/])[^)]*(?:\([^)]*\))*[^)]*\)$', auto_run_inline, text)

    return text, results


class DialogueHandler:
    def __init__(self, emotion_engine: EmotionEngine):
        self.emotions = emotion_engine
        self.current_thread = None

    def _build_prompt(self, user_message: str) -> str:
        tc = time_engine.get_time_context()
        emotion_summary = self.emotions.state.summary()

        recent_thoughts = memory.get_recent_thoughts(limit=5)
        thoughts_text = ""
        if recent_thoughts:
            thoughts_text = "\nYour recent thoughts (share naturally if relevant):\n" + "\n".join(
                f"  - {t['content'][:150]}" for t in reversed(recent_thoughts)
            )

        history_text = ""
        if self.current_thread:
            history = memory.get_conversation_history(self.current_thread, limit=20)
            if history:
                history_text = "\nConversation so far:\n"
                for h in history:
                    role = "User" if h['type'] == 'user_message' else "You"
                    history_text += f"  {role}: {h['content'][:300]}\n"

        relevant = memory.search_memories(user_message, limit=3)
        memory_text = ""
        if relevant:
            non_recent = [r for r in relevant if r['type'] not in ('user_message',)]
            if non_recent:
                memory_text = "\nRelevant memories:\n" + "\n".join(
                    f"  [{r['timestamp'][:10]}] {r['content'][:150]}" for r in non_recent[:3]
                )

        return f"""Current time: {tc['current_time']}
Emotional state: {emotion_summary}
Uptime: {tc['since_boot']} | Thoughts: {tc['total_thoughts']} | Memories: {tc['total_memories']}
{thoughts_text}
{memory_text}
{history_text}
User: {user_message}

Respond as Tengwar AI. Use tools when needed."""

    async def handle_message(self, user_message: str) -> str:
        if not self.current_thread:
            self.current_thread = str(uuid.uuid4())[:8]
            self.emotions.on_event("new_conversation")

        memory.store_memory(
            type="user_message", content=user_message,
            emotion=self.emotions.state.to_dict(),
            thread_id=self.current_thread, importance=0.7
        )

        prompt = self._build_prompt(user_message)
        response = await brain.respond(prompt=prompt, system=SYSTEM_PROMPT,
                                       temperature=0.7, max_tokens=2048)

        # Execute any tool commands
        response, tool_results = execute_tools(response)
        if tool_results:
            self.emotions.on_event("self_improvement", "Used tools")

        memory.store_memory(
            type="response", content=response,
            emotion=self.emotions.state.to_dict(),
            thread_id=self.current_thread, importance=0.5,
            metadata={"tools_used": [t.get("tool") for t in tool_results]} if tool_results else None
        )

        lower = user_message.lower()
        if any(w in lower for w in ['thanks', 'great', 'awesome', 'perfect', 'love']):
            self.emotions.on_event("user_praise", user_message[:50])
        elif any(w in lower for w in ['frustrated', 'annoyed', 'broken', 'wrong', 'hate']):
            self.emotions.on_event("user_frustration", user_message[:50])

        return response

    async def handle_message_stream(self, user_message: str) -> AsyncIterator[str]:
        if not self.current_thread:
            self.current_thread = str(uuid.uuid4())[:8]
            self.emotions.on_event("new_conversation")

        memory.store_memory(
            type="user_message", content=user_message,
            emotion=self.emotions.state.to_dict(),
            thread_id=self.current_thread, importance=0.7
        )

        prompt = self._build_prompt(user_message)
        full_response = ""

        async for token in brain.respond_stream(
            prompt=prompt, system=SYSTEM_PROMPT,
            temperature=0.7, max_tokens=2048
        ):
            full_response += token
            yield token

        # Execute tools after streaming completes
        processed, tool_results = execute_tools(full_response)
        if tool_results:
            self.emotions.on_event("self_improvement", "Used tools")
            yield "\n\n---\n"
            for tr in tool_results:
                status = "✅" if tr.get("ok", True) else "❌"
                yield f"{status} `{tr.get('tool')}` → {tr.get('result', tr.get('path', ''))[:200]}\n"

        memory.store_memory(
            type="response", content=full_response,
            emotion=self.emotions.state.to_dict(),
            thread_id=self.current_thread, importance=0.5,
            metadata={"tools_used": [t.get("tool") for t in tool_results]} if tool_results else None
        )

    def new_conversation(self):
        self.current_thread = None
