from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import re
from dotenv import load_dotenv
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import csv
import os

load_dotenv()

class AgentState(TypedDict, total=False):
    input: str
    seo_evaluation: Optional[str]
    pick_subject: str
    strategist: str
    blog_content: str
    blog_title: str
    SEO_score: int
    related_links: list
    tags: str

def create_workflow_test(api_key, csv_directory, reporter='By Investing', today_date=None):
    if today_date is None:
        from datetime import datetime
        today_date = datetime.now().strftime("%Y-%m-%d")

    llm = ChatGoogleGenerativeAI(model='gemini-1.5-pro', temperature=0.8, google_api_key=api_key)
    workflow = StateGraph(AgentState)

    def trend_analyst_agent(state: AgentState) -> AgentState:
        prompt = ChatPromptTemplate.from_template(
            "다음 뉴스 데이터를 분석하고, 현재 가장 트렌디하고 인기 있는 주제 3개를 선정해주세요:\n{input}\n\n트렌디한 주제 3개:"
        )
        chain = prompt | llm | StrOutputParser()
        pick_subject = chain.invoke({"input": state["input"]})
        return AgentState(input=state["input"], pick_subject=pick_subject)

    def content_strategist_agent(state: AgentState) -> AgentState:
        seo_feedback = state.get("seo_evaluation", "")  # 'seo_evaluation'이 없으면 빈 문자열 반환
        prompt_template = (
            "다음 3개의 트렌디한 주제들을 바탕으로, E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준을 고려하여 각 주제를 요약해주세요. "
            "이 3개의 주제를 연결하여 하나의 블로그 포스트로 작성할 수 있는 방안을 제시해주세요:\n{pick_subject}\n\n전략적 요약 및 연결 방안:"
        )
        if seo_feedback:
            prompt_template += "\n다음 피드백을 바탕으로 글쓰기 전략을 보강하세요: {seo_evaluation}"

        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | llm | StrOutputParser()
        
        invoke_params = {"pick_subject": state["pick_subject"]}
        if seo_feedback:
            invoke_params["seo_evaluation"] = seo_feedback
        
        strategist = chain.invoke(invoke_params)
        
        new_state = dict(state)
        new_state["strategist"] = strategist
        return AgentState(**new_state)

    def blog_writer_agent(state: AgentState) -> AgentState:
        prompt = ChatPromptTemplate.from_template(
            "2000자 이상 2500자 미만으로 작성\n\n"
            "다음 지침에 따라 3개의 주제를 연결한 하나의 블로그 포스트를 작성해주세요. 반드시 아래 형식을 따라주세요:\n\n"
            "제목: [주제를 잘 반영한 제목]\n\n"
            f"내용:\n**{reporter} | {today_date}**\n"
            "[썸네일 이미지]\n"
            "[전체 주제를 요약하는 짧은 도입부]\n\n"
            "### 1. [첫 번째 주제]\n"
            "[관련이미지 설명]\n"
            "[첫 번째 주제에 대한 상세 내용]\n\n"
            "### 2. [두 번째 주제]\n"
            "[관련이미지 설명]\n"
            "[두 번째 주제에 대한 상세 내용]\n\n"
            "### 3. [세 번째 주제]\n"
            "[관련이미지 설명]\n"
            "[세 번째 주제에 대한 상세 내용]\n\n"
            "### 결론: [전체 내용을 종합하는 결론]\n"
            "1. E-E-A-T(경험, 전문성, 권위성, 신뢰성) 기준을 준수하여 전문성과 경험을 보여주는 내용을 포함하세요.\n"
            "2. 독창적이고 고품질의 콘텐츠를 작성하세요.\n"
            "3. 3개의 주제를 자연스럽게 연결하여 하나의 일관된 블로그 포스트로 작성하세요.\n"
            "4. 사용자 경험을 고려하여 읽기 쉽고 유용한 콘텐츠를 만드세요.\n"
            "5. 적절한 키워드를 자연스럽게 사용하세요.\n"
            "주제 및 전략: {strategist}\n\n"
            "블로그 포스트:"
        )
        chain = prompt | llm | StrOutputParser()
        blog_content = chain.invoke({"strategist": state["strategist"]})
        if not blog_content:
            blog_content = "Error: Failed to generate blog content."
        new_state = dict(state)
        new_state["blog_content"] = blog_content
        return AgentState(**new_state)

    def copywriting_agent(state: AgentState) -> AgentState:
        prompt = ChatPromptTemplate.from_template(
            "다음 블로그 포스트 내용을 바탕으로 SEO에 최적화된 매력적인 제목을 1줄로 작성해주세요:\n{blog_content}\n\n제목:"
            "(예시 형식: 글로벌 경제, 불확실성의 그림자: 인플레이션, 금리, 그리고 중국 경제 둔화)"
            "반드시 이모지를 넣지 마세요"
        )
        chain = prompt | llm | StrOutputParser()
        blog_title = chain.invoke({"blog_content": state["blog_content"]})
        new_state = dict(state)
        new_state["blog_title"] = blog_title
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
            "8. 제목의 최적화\n\n"
            "각 항목에 대한 점수와 개선점을 제시한 후, 최종 SEO 점수를 다음 형식으로 반드시 제공해주세요:\n"
            "SEO 점수: [0-100]/100\n"
            "개선점: [간단한 설명]\n\n"
            "블로그 제목: {blog_title}\n"
            "블로그 내용:\n{blog_content}\n\n"
            "SEO 평가:"
        )
        chain = prompt | llm | StrOutputParser()
        seo_evaluation = chain.invoke({"blog_title": state["blog_title"], "blog_content": state["blog_content"]})
        
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
        return AgentState(**new_state)

    def rag_agent(state: AgentState) -> AgentState:
        embeddings = HuggingFaceEmbeddings()
        latest_csv = max([os.path.join(csv_directory, f) for f in os.listdir(csv_directory) if f.endswith('.csv')], key=os.path.getctime)
        
        documents = []
        with open(latest_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                doc = Document(
                    page_content=f"{row['title']} {row['content']}",
                    metadata={"link": row['link']}
                )
                documents.append(doc)

        vectorstore = FAISS.from_documents(documents, embeddings)
        query = f"{state['blog_title']} {state['blog_content']}"
        related_docs = vectorstore.similarity_search(query, k=3)
        related_links = [doc.metadata['link'] for doc in related_docs]
        
        new_state = dict(state)
        new_state["related_links"] = related_links
        return AgentState(**new_state)

    def tag_agent(state: AgentState) -> AgentState:
        prompt = ChatPromptTemplate.from_template(
            "다음 블로그 포스트를 분석하고, 관련된 태그 9개를 작성해주세요. 태그는 쉼표로 구분해주세요.\n"
            "블로그 제목: {blog_title}\n"
            "블로그 내용:\n{blog_content}\n\n"
            "태그 (예시 형식: 태그1,태그2,태그3,...태그9):"
        )
        chain = prompt | llm | StrOutputParser()
        tags = chain.invoke({"blog_title": state["blog_title"], "blog_content": state["blog_content"]})
        new_state = dict(state)
        new_state["tags"] = tags
        return AgentState(**new_state)

    workflow.add_node("trend_analyst", trend_analyst_agent)
    workflow.add_node("content_strategist", content_strategist_agent)
    workflow.add_node("blog_writer", blog_writer_agent)
    workflow.add_node("copywriting", copywriting_agent)
    workflow.add_node("seo_evaluator", seo_evaluator_agent)
    workflow.add_node("rag", rag_agent)
    workflow.add_node("tag", tag_agent)

    workflow.set_entry_point("trend_analyst")
    workflow.add_edge("trend_analyst", "content_strategist")
    workflow.add_edge("content_strategist", "blog_writer")
    workflow.add_edge("blog_writer", "copywriting")
    workflow.add_edge("copywriting", "seo_evaluator")

    def route_based_on_seo(state):
        return "rag" if state["SEO_score"] >= 70 else "content_strategist"

    workflow.add_conditional_edges(
        "seo_evaluator",
        route_based_on_seo,
        {
            "rag": "rag",
            "content_strategist": "content_strategist"
        }
    )

    workflow.add_edge("rag", "tag")
    workflow.add_edge("tag", END)

    return workflow.compile()

def run_workflow_test(workflow, input_data, result_directory):
    state = AgentState(input=input_data)
    final_state = {'input': input_data}
    for step in workflow.stream(state):
        for key, value in step.items():
            if key != 'input':
                print(f"Step completed: {key}")
                if key == "trend_analyst":
                    print("Selected subjects:", value.get("pick_subject", "No subjects selected"))
                elif key == "content_strategist":
                    print("Content strategy:", value.get("strategist", "No strategy provided"))
                elif key == "blog_writer":
                    blog_content = value.get("blog_content")
                    if blog_content is not None:
                        print("Blog content written. Length:", len(blog_content))
                        with open(os.path.join(result_directory, "blog_content.txt"), "w", encoding="utf-8") as f:
                            f.write(blog_content)
                    else:
                        print("Warning: Blog content is None")
                elif key == "copywriting":
                    blog_title = value.get("blog_title")
                    if blog_title:
                        print("Blog title:", blog_title)
                        with open(os.path.join(result_directory, "blog_title.txt"), "w", encoding="utf-8") as f:
                            f.write(blog_title)
                    else:
                        print("Warning: Blog title is None or empty")
                elif key == "seo_evaluator":
                    print("SEO score:", value.get("SEO_score", "No score provided"))
                elif key == "rag":
                    related_links = value.get("related_links", [])
                    print("Related links found:", related_links)
                    with open(os.path.join(result_directory, "related_links.txt"), "w", encoding="utf-8") as f:
                        for link in related_links:
                            f.write(f"{link}\n")
                elif key == "tag":
                    tags = value.get("tags", "No tags provided")
                    print("Tags generated:", tags)
                    with open(os.path.join(result_directory, "tags.txt"), "w", encoding="utf-8") as f:
                        f.write(tags)
                print("-" * 50)
                final_state.update(value)
        if END in step:
            break
    return final_state