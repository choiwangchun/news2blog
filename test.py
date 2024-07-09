import os
import glob
from datetime import datetime
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import pandas as pd
import re

load_dotenv()

reporter = 'AI기자 choi'
today_date = datetime.now().strftime("%Y-%m-%d")

class AgentState(TypedDict, total=False):
    input: str
    pick_subject: str
    strategist: str
    blog_output: str
    SEO_score: int
    seo_evaluation: str

def get_latest_csv(directory):
    csv_files = glob.glob(os.path.join(directory, '*.csv'))
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the directory.")
    return max(csv_files, key=os.path.getctime)

def read_csv_file(file_path):
    df = pd.read_csv(file_path)
    return df.to_string(index=False)

llm = ChatGoogleGenerativeAI(model='gemini-1.5-pro', temperature=0.8, google_api_key=os.getenv('GOOGLE_API_KEY'))

workflow = StateGraph(AgentState)

def trend_analyst_agent(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template(
        "다음 뉴스 데이터를 분석하고, 현재 가장 트렌디하고 인기 있는 주제 3개를 선정해주세요:\n{input}\n\n트렌디한 주제 3개:"
    )
    chain = prompt | llm | StrOutputParser()
    pick_subject = chain.invoke({"input": state["input"]})
    return AgentState(input=state["input"], pick_subject=pick_subject)

def content_strategist_agent(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template(
        "다음 3개의 트렌디한 주제들을 바탕으로, E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준을 고려하여 각 주제를 요약해주세요. "
        "이 3개의 주제를 연결하여 하나의 블로그 포스트로 작성할 수 있는 방안을 제시해주세요:\n{pick_subject}\n\n전략적 요약 및 연결 방안:"
    )
    chain = prompt | llm | StrOutputParser()
    strategist = chain.invoke({"pick_subject": state["pick_subject"]})
    
    # 기존 상태를 복사하고 새로운 값을 업데이트
    new_state = dict(state)
    new_state["strategist"] = strategist
    return AgentState(**new_state)

def blog_writer_agent(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template(
        "다음 지침과 search engine optimization점수를 최대한 높힐 수있는 방법을 생각하여 3개의 주제를 연결한 하나의 블로그 포스트를 작성해주세요:\n"
        "1. E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준을 준수하여 전문성과 경험을 보여주는 내용을 포함하세요.\n"
        "2. 독창적이고 고품질의 콘텐츠를 작성하세요.\n"
        f"3. 작성자 정보는 {reporter}로 해주고 날짜는 {today_date}로 표시하세요.\n"
        "4. 3개의 주제를 자연스럽게 연결하여 하나의 일관된 블로그 포스트로 작성하세요.\n"
        "5. 글의 구조는 도입부, 각 주제별 본문, 그리고 3개 주제를 종합한 결론으로 구성하세요.\n"
        "6. 사용자 경험을 고려하여 읽기 쉽고 유용한 콘텐츠를 만드세요.\n"
        "7. 적절한 키워드를 자연스럽게 사용하세요.\n\n"
        "주제 및 전략: {strategist}\n\n"
        "블로그 포스트:"
    )
    chain = prompt | llm | StrOutputParser()
    blog_output = chain.invoke({"strategist": state["strategist"]})
    new_state = dict(state)
    new_state["blog_output"] = blog_output
    return AgentState(**new_state)

def seo_evaluator_agent(state: AgentState) -> AgentState:
    prompt = ChatPromptTemplate.from_template(
        "다음 기준에 따라 블로그 포스트의 SEO(검색 엔진 최적화) 점수를 0에서 100 사이의 정수로 평가해주세요:\n"
        "1. E-E-A-T (경험, 전문성, 권위성, 신뢰성) 준수 여부\n"
        "2. 콘텐츠의 독창성과 품질\n"
        "3. 작성자 정보와 날짜 표시의 명확성\n"
        "4. YMYL(Your Money Your Life) 주제에 대한 적절한 처리\n"
        "5. 주제의 일관성과 집중도\n"
        "6. 사용자 경험과 가독성\n"
        "7. 키워드 사용의 적절성\n"
        "8. 메타 데이터 (제목, 설명 등)의 최적화\n\n"
        "각 항목에 대한 점수와 개선점을 제시한 후, 최종 SEO 점수를 다음 형식으로 반드시 제공해주세요:\n"
        "SEO 점수: [0-100]/100\n"
        "개선점: [간단한 설명]\n\n"
        "블로그 포스트:\n{blog_output}\n\n"
        "SEO 평가:"
    )
    chain = prompt | llm | StrOutputParser()
    seo_evaluation = chain.invoke({"blog_output": state["blog_output"]})
    
    try:
        score_match = re.search(r'SEO 점수:\s*(\d+)(?:/100)?', seo_evaluation, re.IGNORECASE)
        if score_match:
            SEO_score = int(score_match.group(1))
        else:
            raise ValueError("SEO score not found in the evaluation")
    except Exception as e:
        print(f"Failed to parse SEO score: {e}")
        print("SEO evaluation:", seo_evaluation)
        SEO_score = 0
    
    new_state = dict(state)
    new_state["SEO_score"] = SEO_score
    new_state["seo_evaluation"] = seo_evaluation
    return AgentState(**new_state)

workflow.add_node("trend_analyst", trend_analyst_agent)
workflow.add_node("content_strategist", content_strategist_agent)
workflow.add_node("blog_writer", blog_writer_agent)
workflow.add_node("seo_evaluator", seo_evaluator_agent)

workflow.set_entry_point("trend_analyst")
workflow.add_edge("trend_analyst", "content_strategist")
workflow.add_edge("content_strategist", "blog_writer")
workflow.add_edge("blog_writer", "seo_evaluator")

def route_based_on_seo(state):
    return END if state["SEO_score"] >= 70 else "content_strategist"

workflow.add_conditional_edges(
    "seo_evaluator",
    route_based_on_seo,
    {
        END: END,
        "content_strategist": "content_strategist"
    }
)

app = workflow.compile()

def run_workflow(input_data):
    state = AgentState(input=input_data)
    final_state = {}
    for step in app.stream(state):
        for key, value in step.items():
            if key != 'input':
                print(f"Step completed: {key}")
                if key == "trend_analyst":
                    print("Selected subjects:", value["pick_subject"])
                elif key == "content_strategist":
                    print("Content strategy:", value["strategist"])
                elif key == "blog_writer":
                    print("Blog post written. Length:", len(value["blog_output"]))
                elif key == "seo_evaluator":
                    print("SEO score:", value["SEO_score"])
                    print("SEO evaluation:", value["seo_evaluation"])
                print("-" * 50)
                final_state.update(value)
        if END in step:
            break
    return final_state

if __name__ == "__main__":
    csv_directory = r"C:\Users\slek9\PycharmProjects\news2blog\parsing_news"
    latest_csv = get_latest_csv(csv_directory)
    input_data = read_csv_file(latest_csv)
    result = run_workflow(input_data)
    
    print("\nFinal Blog Post (Markdown format):")
    if "blog_output" in result:
        print("```markdown")
        print(result["blog_output"])
        print("```")
    else:
        print("Error: Blog output not generated. Workflow may have failed.")
    
    if "SEO_score" in result:
        print(f"\nFinal SEO Score: {result['SEO_score']}")
    else:
        print("Error: SEO score not available. Workflow may have failed.")