from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import csv
import os

class TestNewsBot:
    def __init__(self):
        self.csv_directory = r"C:\Users\slek9\PycharmProjects\news2blog\parsing_news"
        self.embeddings = HuggingFaceEmbeddings()

    def get_latest_csv(self, directory):
        csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError("No CSV files found in the directory.")
        
        latest_file = max(csv_files, key=lambda x: os.path.getctime(os.path.join(directory, x)))
        return os.path.join(directory, latest_file)

    def get_related_links(self, title, content):
        latest_csv = self.get_latest_csv(self.csv_directory)
        
        # CSV 파일에서 뉴스 기사 읽기
        documents = []
        with open(latest_csv, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                doc = Document(
                    page_content=f"{row['title']} {row['content']}",
                    metadata={"link": row['link']}
                )
                documents.append(doc)

        # FAISS 벡터 저장소 생성
        vectorstore = FAISS.from_documents(documents, self.embeddings)

        # 블로그 포스트 내용으로 유사한 문서 검색
        query = f"{title} {content}"
        related_docs = vectorstore.similarity_search(query, k=3)

        # 관련 링크 추출
        related_links = [doc.metadata['link'] for doc in related_docs]
        
        return related_links

def main():
    test_bot = TestNewsBot()
    
    # 테스트용 제목과 내용
    test_title = "글로벌 경제, 불확실성의 그림자: 인플레이션, 금리, 그리고 중국 경제 둔화"
    test_content = """**By Investing | 2024-07-10**

    [**썸네일 이미지 설명: 어두운 배경에 세계 지도와 하락하는 화살표 그래프, 흐릿한 사람들 실루엣**]

    전 세계적인 인플레이션 완화 추세에도 불구하고 경기 침체 우려는 여전히 남아있습니다. 특히 중국 경제 회복 둔화는 글로벌 경제에 불확실성을 더하는 요인입니다. 이 글에서는 현재 글로벌 경제 상황을 3가지 키워드 - 인플레이션, 금리, 중국 - 를 중심으로 분석하고 앞으로의 전망을 살펴보겠습니다.

    ### 1. 인플레이션, 진정 국면? 아직 안심하기 일러…

    [**이미지 설명: 상승하는 물가 그래프와 함께 마트에서 장을 보며 걱정하는 사람들**]

    최근 미국 소비자물가지수(CPI) 상승률이 둔화하며 인플레이션이 정점을 지났다는 분석이 나오고 있습니다. 하지만,  근원 물가 상승률은 여전히 높은 수준이며, 러시아-우크라이나 전쟁 장기화, 공급망 불안 등 변수가 많아 안심하기는 이릅니다. 국제통화기금(IMF)은 올해 세계 경제 성장률 전망치를 하향 조정하며 인플레이션의 하방 리스크를 경고했습니다. 특히 에너지 및 식료품 가격 변동성이 커지면서 저소득 국가를 중심으로 경제적 어려움이 가중될 수 있다는 우려가 제기되고 있습니다.

    ### 2. 긴축 정책, 언제까지? 시장의 눈은 연준으로…

    [**이미지 설명: 미국 연방준비제도 건물 사진과 함께 금리 인상을 나타내는 그래프**]

    미국 연방준비제도(Fed)는 인플레이션을 잡기 위해 공격적인 금리 인상을 단행해왔습니다.  최근 제롬 파월 연준 의장은 9월 연방공개시장위원회(FOMC)에서 금리 인상을 중단할 가능성을 시사했지만,  "인플레이션이 목표 수준으로 지속적으로 하락하고 있다는 확신이 들 때까지 긴축적인 정책 기조를 유지할 것"이라고 강조했습니다. 시장에서는 9월 금리 인상 동결 가능성을 높게 점치고 있지만, 향후 발표될 경제 지표와 연준 위원들의 발언에 따라 금리 인하 시점에 대한 전망은 달라질 수 있습니다.  

    ### 3. '세계의 공장' 멈추나? 중국 경제 둔화, 글로벌 경제에 미치는 영향은?

    [**이미지 설명: 멈춰있는 공장 사진과 함께 하락하는 중국 경제 성장률 그래프**]

    세계 경제 성장의 엔진 역할을 해왔던 중국 경제가 좀처럼 활력을 찾지 못하고 있습니다.  6월 중국 소비자물가지수(CPI) 상승률은 전년 동월 대비 0%를 기록하며 디플레이션 우려까지 제기되고 있습니다. 부동산 경기 침체 장기화, 청년 실업률 증가, 소비 심리 위축 등이 겹치면서 중국 경제 회복이 지연될 수 있다는 전망이 나옵니다. 중국은 세계 원자재 수요의 상당 부분을 차지하고 있어, 중국 경제 둔화는 글로벌 원자재 시장에도 부정적인 영향을 미칠 수 있습니다. 

    ### 4. 불확실성 속에서 우리는?

    [**이미지 설명: 다양한 투자 포트폴리오를 보여주는 이미지**]

    현재 글로벌 경제는 인플레이션 완화, 금리 인상 사이클 종료 기대감, 중국 경제 둔화 우려 등  복합적인 요인들이 작용하며 불확실성이 높은 상황입니다. 투자자들은 변동성 확대 가능성에 대비해야 하며,  경제 지표 발표,  중앙은행들의 통화 정책 변화, 지정학적 리스크 등을 예의주시할 필요가 있습니다. 또한, 분산 투자,  가치주 중심의 투자 전략을 통해 리스크 관리에 힘써야 할 것입니다."""
    
    # 관련 링크 가져오기
    related_links = test_bot.get_related_links(test_title, test_content)

    # 결과 출력
    print("테스트 제목:", test_title)
    print("테스트 내용:", test_content)
    print("\n관련 링크:")
    for i, link in enumerate(related_links, 1):
        print(f"{i}. {link}")

if __name__ == "__main__":
    main()