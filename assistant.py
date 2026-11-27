"""터미널 AI 비서 (Claude API, 스트리밍 + 대화 기억).

실행:  python assistant.py
종료:  /quit   초기화: /reset
"""
import anthropic

MODEL = "claude-opus-5-5"
SYSTEM = (
    "당신은 친절하고 유능한 한국어 AI 비서입니다. "
    "사용자의 질문에 정확하고 간결하게 답하고, 모호하면 짧게 되물어보세요."
)

client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 또는 `ant auth login` 사용


def reply(messages: list) -> str:
    """대화 기록을 보내 스트리밍으로 출력하고 전체 응답 텍스트를 반환."""
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=SYSTEM,
        messages=messages,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # 안전 필터로 거절될 때 자동 대체 모델 사용
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
        final = stream.get_final_message()
    print()
    if final.stop_reason == "refusal":
        return "(요청을 처리할 수 없습니다.)"
    return "".join(b.text for b in final.content if b.type == "text")


def main() -> None:
    messages: list = []
    print("AI 비서입니다. /quit 종료, /reset 대화 초기화")
    while True:
        try:
            user = input("\n나> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user == "/quit":
            break
        if user == "/reset":
            messages.clear()
            print("대화를 초기화했습니다.")
            continue
        messages.append({"role": "user", "content": user})
        print("비서> ", end="", flush=True)
        try:
            answer = reply(messages)
        except anthropic.AuthenticationError:
            print("\nAPI 키가 없거나 잘못되었습니다. ANTHROPIC_API_KEY를 설정하세요.")
            messages.pop()
            continue
        except anthropic.RateLimitError:
            print("\n요청이 너무 많습니다. 잠시 후 다시 시도하세요.")
            messages.pop()
            continue
        except anthropic.APIConnectionError:
            print("\n네트워크 오류입니다.")
            messages.pop()
            continue
        except anthropic.APIStatusError as e:
            print(f"\nAPI 오류({e.status_code}): {e.message}")
            messages.pop()
            continue
        messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
