from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Any
from operator import itemgetter
from langchain_google_genai import ChatGoogleGenerativeAI

class AgentState(TypedDict):
    input: str
    output: Any

def create_workflow(api_key):
    llm = ChatGoogleGenerativeAI(model='gemini-1.5-pro', temperature=0.8, google_api_key=api_key)

    workflow = StateGraph(AgentState)

    def create_agent(prompt_template):
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm
        return lambda state: {"input": state["input"], "output": chain.invoke({"input": state["input"]}).content}

    # 노드 추가
    workflow.add_node("trend_analyst", create_agent("다음 뉴스 데이터를 분석하고, 현재 가장 트렌디하고 인기 있는 주제 5개를 선정해주세요:\n{input}\n\n트렌디한 주제 5개:"))
    workflow.add_node("content_strategist", create_agent("다음 트렌디한 주제들을 바탕으로, 사람들이 가장 관심을 가질 만한 측면에 초점을 맞춰 각 주제를 요약해주세요. 각 요약은 독자의 호기심을 자극하고 클릭을 유도할 수 있도록 작성해주세요:\n{input}\n\n전략적 요약:"))
    workflow.add_node("blog_writer", create_agent("다음 전략적 요약을 바탕으로 흥미로운 블로그 포스트를 작성해주세요. 독자의 관심을 끌고 유지할 수 있도록 내용을 구성해주세요:\n{input}\n\n블로그 포스트:"))
    workflow.add_node("seo_evaluator", create_agent("다음 블로그 포스트의 SEO 점수를 0에서 100 사이로 평가해주세요. 평가 기준에는 키워드 사용, 제목의 매력도, 내용의 가독성, 독자 참여 유도 등이 포함되어야 합니다:\n{input}\n\nSEO 점수 및 개선점:"))

    # 엣지 연결
    workflow.set_entry_point("trend_analyst")
    workflow.add_edge("trend_analyst", "content_strategist")
    workflow.add_edge("content_strategist", "blog_writer")
    workflow.add_edge("blog_writer", "seo_evaluator")

    # SEO 점수에 따른 조건부 엣지
    def route_based_on_seo(state):
        seo_output = state["seo_evaluator"]["output"]
        score = int(seo_output.split()[0])
        if score >= 80:
            return END
        else:
            return "content_strategist"

    workflow.add_conditional_edges(
        "seo_evaluator",
        route_based_on_seo,
        {
            END: END,
            "content_strategist": "content_strategist"
        }
    )

    return workflow.compile()

def run_workflow(app, input_data):
    result = {}
    for step in app.stream({"input": input_data, "output": None}):
        for key, value in step.items():
            if key != 'input':
                result[key] = value
        if END in step:
            break
    return result