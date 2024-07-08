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

    # TrendAnalystAgent 정의
    def trend_analyst_agent(state):
        prompt = ChatPromptTemplate.from_template(
            "다음 뉴스 데이터를 분석하고, 현재 가장 트렌디하고 인기 있는 주제 5개를 선정해주세요:\n{input}\n\n트렌디한 주제 5개:"
        )
        chain = prompt | llm
        output = chain.invoke({"input": state["input"]}).content
        return {"input": state["input"], "output": output}

    # ContentStrategistAgent 정의
    def content_strategist_agent(state):
        prompt = ChatPromptTemplate.from_template(
            "다음 트렌디한 주제들을 바탕으로, E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준을 고려하여 각 주제를 요약해주세요. "
            "독자의 관심을 끌 수 있는 독창적인 내용으로 구성하세요:\n{input}\n\n전략적 요약:"
        )
        chain = prompt | llm
        output = chain.invoke({"input": state["input"]}).content
        return {"input": state["input"], "output": output}

    # BlogWriterAgent 정의
    def blog_writer_agent(state):
        prompt = ChatPromptTemplate.from_template(
            "다음 지침을 따라 블로그 포스트를 작성해주세요:\n"
            "1. E-E-A-T 기준을 준수하여 전문성과 경험을 보여주는 내용을 포함하세요.\n"
            "2. 독창적이고 고품질의 콘텐츠를 작성하세요. 특히 짧은 내용의 경우 독창성에 주의를 기울이세요.\n"
            "3. 작성자 정보와 날짜를 명확히 표시하세요.\n"
            "4. 주제와 관련된 신뢰할 수 있는 외부 링크를 포함하세요.\n"
            "5. YMYL(Your Money Your Life) 주제에 대해 특별히 주의를 기울이세요.\n"
            "6. 글의 주제에 집중하고 일관성을 유지하세요.\n"
            "7. 사용자 경험을 고려하여 읽기 쉽고 유용한 콘텐츠를 만드세요.\n"
            "8. 적절한 키워드를 자연스럽게 사용하세요.\n\n"
            "주제: {input}\n\n"
            "블로그 포스트:"
        )
        chain = prompt | llm
        output = chain.invoke({"input": state["input"]}).content
        return {"input": state["input"], "output": output}

    # SEOEvaluatorAgent 정의
    def seo_evaluator_agent(state):
        prompt = ChatPromptTemplate.from_template(
            "다음 기준에 따라 블로그 포스트의 SEO 점수를 0에서 100 사이의 정수로 평가해주세요:\n"
            "1. E-E-A-T (경험, 전문성, 권위성, 신뢰성) 준수 여부\n"
            "2. 콘텐츠의 독창성과 품질\n"
            "3. 작성자 정보와 날짜 표시의 명확성\n"
            "4. 관련성 있는 외부 링크 포함 여부\n"
            "5. YMYL(Your Money Your Life) 주제에 대한 적절한 처리\n"
            "6. 주제의 일관성과 집중도\n"
            "7. 사용자 경험과 가독성\n"
            "8. 키워드 사용의 적절성\n"
            "9. 메타 데이터 (제목, 설명 등)의 최적화\n"
            "10. 모바일 친화성\n\n"
            "각 항목에 대한 점수와 개선점을 제시한 후, 최종 SEO 점수를 다음 형식으로 제공해주세요:\n"
            "SEO 점수: [0-100 사이의 정수]\n"
            "개선점: [간단한 설명]\n\n"
            "블로그 포스트:\n{input}\n\n"
            "SEO 평가:"
        )
        chain = prompt | llm
        output = chain.invoke({"input": state["input"]}).content
        
        # SEO 점수 추출
        try:
            score_line = [line for line in output.split('\n') if line.startswith("SEO 점수:")][0]
            score = int(score_line.split(":")[1].strip())
        except (ValueError, IndexError):
            print(f"Failed to parse SEO score from: {output}")
            score = 0
        
        return {"input": state["input"], "output": {"score": score, "feedback": output}}

    # 노드 추가
    workflow.add_node("trend_analyst", trend_analyst_agent)
    workflow.add_node("content_strategist", content_strategist_agent)
    workflow.add_node("blog_writer", blog_writer_agent)
    workflow.add_node("seo_evaluator", seo_evaluator_agent)

    # 엣지 연결
    workflow.set_entry_point("trend_analyst")
    workflow.add_edge("trend_analyst", "content_strategist")
    workflow.add_edge("content_strategist", "blog_writer")
    workflow.add_edge("blog_writer", "seo_evaluator")

    # SEO 점수에 따른 조건부 엣지
    def route_based_on_seo(state):
        seo_score = state["seo_evaluator"]["output"]["score"]
        if seo_score >= 80:
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
        print(f"Step completed: {key}")  # 디버깅을 위한 출력 추가
        if END in step:
            break
    print(f"Final result: {result}")  # 최종 결과 출력
    return result