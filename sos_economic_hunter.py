import yfinance as yf
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import json
import ssl
import os
import requests

ssl._create_default_https_context = ssl._create_unverified_context

def get_fear_greed_index():
    try:
        # Using a reliable third-party API for CNN Fear & Greed Index
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data and "data" in data:
            latest = data["data"][0]
            value = int(latest["value"])
            classification = latest["value_classification"]
            return {"value": value, "classification": classification}
    except Exception as e:
        print(f"공포와 탐욕 지수 수집 오류: {e}")
    return None

def get_market_data():
    symbols = {
        '나스닥': '^IXIC',
        'S&P 500': '^GSPC',
        '다우존스': '^DJI',
        '코스피': '^KS11',
        '코스닥': '^KQ11',
        'VIX (변동성 지수)': '^VIX',
        '미국 10년물 국채금리': '^TNX',
        '미국 2년물 국채금리': '^IRX',
        '원/달러 환율': 'KRW=X',
        '유로스톡스50': '^STOXX50E',
        '상해종합': '000001.SS',
        '니케이225': '^N225',
        '항셍': '^HSI',
        '비트코인': 'BTC-USD',
        '이더리움': 'ETH-USD',
        'WTI 원유': 'CL=F',
        '금': 'GC=F',
        '은': 'SI=F',
        '구리': 'HG=F',
        '엔비디아': 'NVDA',
        'TSMC': 'TSM',
        'ASML': 'ASML',
        '삼성전자': '005930.KS',
        'SK하이닉스': '000660.KS',
        '현대차': '005380.KS',
        '테슬라': 'TSLA',
        '인도 닙티50': '^NSEI'
    }
    
    results = {}
    for name, ticker in symbols.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                results[name] = {"price": last_close, "change": change_pct}
            else:
                results[name] = {"error": "데이터 부족"}
        except Exception as e:
            results[name] = {"error": str(e)}
            
    kospi_top_symbols = {
        'LG에너지솔루션': '373220.KS',
        '삼성바이오로직스': '207940.KS',
        '기아': '000270.KS',
        'KB금융': '105560.KS',
        '신한지주': '055550.KS',
        '하나금융지주': '086790.KS'
    }
    for name, ticker in kospi_top_symbols.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                change_pct = ((last_close - prev_close) / prev_close) * 100
                results[name] = {"price": last_close, "change": change_pct}
        except:
            pass

    return results

def get_news(query, count=4):
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        news_items = []
        for item in root.findall('.//item')[:count]:
            title = item.find('title').text
            link = item.find('link').text
            # Remove source name from title if possible (Google News usually puts it at the end)
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            news_items.append({"title": title, "link": link})
        return news_items
    except Exception as e:
        return []

def get_hunter_insight(market_data):
    """
    Generates a simple investment insight based on key market indicators.
    """
    try:
        sp500_change = market_data.get('S&P 500', {}).get('change', 0)
        nasdaq_change = market_data.get('나스닥', {}).get('change', 0)
        yield_change = market_data.get('미국 10년물 국채금리', {}).get('change', 0)
        
        insight = ""
        if sp500_change > 0.5 and nasdaq_change > 0.5:
            insight = "뉴욕 증시는 기술주 중심의 강한 매수세로 마감했습니다. 리스크 온 심리가 강해지며 국내 증시에도 긍정적인 영향이 예상됩니다."
        elif sp500_change < -0.5:
            insight = "해외 증시의 하락 압력이 거세지고 있습니다. 금리 변동성에 유의하며 방어적인 포트폴리오 유지가 필요해 보입니다."
        elif yield_change > 1:
            insight = "국채 금리의 급등이 성장주에 하방 압력을 가하고 있습니다. 금리 민감주 및 가치주로의 비중 조절을 검토할 시점입니다."
        else:
            insight = "시장이 뚜렷한 방향성 없이 관망세를 보이고 있습니다. 주요 경제 지표 발표 전까지 개별 종목 장세가 이어질 것으로 보입니다."
            
        return insight
    except:
        return "시장 데이터 분석 중입니다. 신중한 투자 결정을 권고드립니다."

def summarize_news(news_items, theme_name):
    """
    Summarizes a list of news items into a concise thematic summary.
    This is a simplified version; in a production environment, this could use an LLM.
    """
    if not news_items:
        return f"• {theme_name}: 관련 소식을 찾지 못했습니다."
    
    # Extract key keywords/themes from titles (simplified summarization)
    summary_parts = []
    for item in news_items:
        title = item['title']
        # Remove common fluff
        title = title.replace("[속보]", "").replace("단독", "").strip()
        summary_parts.append(title)
    
    # Return a grouped string of titles/summaries
    joined_summaries = "\n  - ".join(summary_parts)
    return f"• **{theme_name}** 주요 소식:\n  - {joined_summaries}"

def get_rss_news(url, count=4):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        news_items = []
        # Support both RSS 2.0 and Atom
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        for item in items[:count]:
            title_node = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            link_node = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
            
            title = title_node.text if title_node is not None else "No Title"
            link = ""
            if link_node is not None:
                link = link_node.text if link_node.text else link_node.get('href', '')
                
            news_items.append({"title": title, "link": link})
        return news_items
    except Exception as e:
        return [{"title": f"RSS 수집 오류: {e}", "link": ""}]
def get_portfolio_data():
    portfolio = {
        'KODEX 은행': '091220.KS',
        'ACE 미국배당다우존스': '447770.KS',
        'TIMEFOLIO 미국배당다우존스액티브': '465580.KS',
        'KODEX 인도Nifty50': '453870.KS',
        '삼성전자': '005930.KS',
        'KT&G': '033780.KS',
        '현대차2우B': '005387.KS',
        'PLUS 고배당주': '140700.KS',
        'KODEX 미국나스닥100': '133690.KS',
        'ACE 글로벌반도체Top4': '446700.KS',
        'TIGER 미국나스닥100커버드콜': '441680.KS',
        'TIGER 미국나스닥100타겟데일리': '486290.KS',
        'GOF': 'GOF',
        '리얼티인컴': 'O',
        'XLV': 'XLV'
    }
    
    alerts = []
    for name, ticker in portfolio.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                last_close = float(hist['Close'].iloc[-1])
                prev_close = float(hist['Close'].iloc[-2])
                change_pct = ((last_close - prev_close) / prev_close) * 100
                if change_pct <= -5.0:
                    alerts.append(f"🚨 **{name}**: 급락 경고! ({change_pct:.2f}%) - 리밸런싱 검토 필요")
        except:
            pass
            
    news_query = "특징주 악재 호재 (삼성전자 OR 배당주 OR 금리 OR 리얼티인컴 OR 반도체)"
    portfolio_news = get_news(news_query, count=3)
    
    return alerts, portfolio_news

def get_economic_calendar():
    # Simple mock-up or targeted search for economic events
    # Real-time API would be better, but for now we search for upcoming events
    try:
        events = get_news("이번주 주요 경제 일정 CPI FOMC 금리 발표", count=3)
        return events
    except:
        return []

def generate_markdown_report(market_data, news_data, portfolio_alerts, portfolio_news, fng_index, economic_events):
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    report = f"# So's SOS 일일 경제 브리핑 ({today_date} 아침)\n"
    report += "**작성자:** So's SOS 경제사냥꾼 🕵️‍♂️📈\n\n---\n\n"
    
    # 1. 글로벌 증시 및 경제 동향
    report += "## 1. 글로벌 증시 및 경제 동향 🌎\n\n"
    
    # 1-1. 해외 주요지수 마감 현황
    report += "### 1-1. 해외 주요지수 마감 현황\n"
    def get_data_line(name, symbol_name=None):
        search_name = symbol_name if symbol_name else name
        if search_name not in market_data or "error" in market_data[search_name]:
            return None
        d = market_data[search_name]
        price = d['price']
        change = d['change']
        sign = "▲" if change > 0 else "▼" if change < 0 else "-"
        
        if '금리' in name:
            return f"* **{name}:** {price:.3f}% ({sign} {'상승' if change > 0 else '하락' if change < 0 else '보합'})"
        elif '원/달러' in name:
             return f"* **{name}:** {price:,.2f}원 ({sign} {abs(price * (change/100)):.2f}원)"
        elif '비트코인' in name:
             return f"* **{name}:** 약 ${price:,.0f} ({sign} {abs(change):.1f}%{' 하락' if change < 0 else ' 상승'})"
        return f"* **{name}:** {price:,.2f} ({sign} {abs(change):.2f}%)"

    indices = [
        ('나스닥 (NASDAQ)', '나스닥'),
        ('S&P 500', 'S&P 500'),
        ('다우존스 산업평균', '다우존스'),
        ('VIX (변동성 지수)', 'VIX (변동성 지수)'),
        ('미국 10년물 국채금리', '미국 10년물 국채금리'),
        ('미국 2년물 국채금리', '미국 2년물 국채금리'),
        ('원/달러 환율', '원/달러 환율'),
        ('암호화폐 (비트코인)', '비트코인')
    ]
    for name, sym in indices:
        line = get_data_line(name, sym)
        if line: report += line + "\n"
    
    report += "* **원자재:**\n"
    commodities = [('WTI 원유', '$'), ('국제 금', '/oz'), ('국제 은', '/oz'), ('구리', '/lb')]
    for comm, unit in commodities:
        d = market_data.get(comm)
        if d and "error" not in d:
            sign = "▲" if d['change'] > 0 else "▼" if d['change'] < 0 else "-"
            val_prefix = "$" if unit == '$' else ""
            val_suffix = "" if unit == '$' else unit
            report += f"    * **{comm}:** {val_prefix}{d['price']:,.2f}{val_suffix} ({sign} {abs(d['change']):.2f}%)\n"
    
    # 1-2. 해외 주요 뉴스 및 매크로 이슈
    report += "\n### 1-2. 해외 주요 뉴스 및 매크로 이슈\n"
    report += summarize_news(news_data.get("글로벌 경제 및 주요 이슈", []), "주요 매크로 이슈") + "\n"
    report += summarize_news(news_data.get("CNBC World News", []), "Global Headlines (CNBC/KED)") + "\n"
    
    report += "\n---\n\n## 2. 국내 증시 주요 이슈 🇰🇷\n\n"
    
    # 2-1. 코스피/코스닥
    report += "### 2-1. 코스피/코스닥 주요 지수 및 특징주\n"
    kp = market_data.get('코스피')
    kd = market_data.get('코스닥')
    if kp and kd and "error" not in kp and "error" not in kd:
        report += f"* **코스피:** {kp['price']:,.2f} ({'▲' if kp['change'] > 0 else '▼'} {abs(kp['change']):.2f}%) / **코스닥:** {kd['price']:,.2f} ({'▲' if kd['change'] > 0 else '▼'} {abs(kd['change']):.2f}%)\n"
    report += summarize_news(news_data.get("매일경제 (MK) 헤드라인", []), "특징주 및 시장 동향") + "\n"
    
    # 2-2. 정책 및 현안
    report += "\n### 2-2. 주식시장 정책 및 현안\n"
    report += summarize_news(news_data.get("한국경제 (Hankyung) 금융", []), "밸류업 및 정책 현안") + "\n"

    report += "\n---\n\n## 3. 관심분야 트래킹 🎯\n\n"
    
    # 3-1. 반도체
    report += "### 3-1. 반도체 (엔비디아, TSMC, 삼성전자, SK하이닉스 등)\n"
    report += summarize_news(news_data.get("반도체 및 나스닥 테마", []), "반도체 주요 이슈") + "\n"
    
    # 3-2. 국내 배당주
    report += "\n### 3-2. 국내 배당주 (PLUS 고배당주, 금융지주, 은행주)\n"
    report += summarize_news(news_data.get("포트폴리오 뉴스", []), "배당주 및 금융주 동향") + "\n"
    
    # 3-3. 기타 관심종목
    report += "\n### 3-3. 기타 관심종목 (현대차, 테슬라, 인도시장 등)\n"
    report += summarize_news(news_data.get("HBF 관련 뉴스", []), "기타 관심 섹터") + "\n"

    # 3-4. 모니터링
    report += "\n### 3-4. 보유/관심종목 모니터링 (리밸런싱 점검)\n"
    if "한경 컨센서스 (최신)" in news_data:
        report += "*증권사 리서치 및 보고서*\n"
        for item in news_data["한경 컨센서스 (최신)"]:
            report += f"* [{item['title']}]({item['link']})\n"
    
    if economic_events:
        report += "\n*주요 경제 일정*\n"
        for event in economic_events:
            report += f"* [{event['title']}]({event['link']})\n"

    if portfolio_alerts:
        report += "\n*🚨 포트폴리오 알림*\n"
        for alert in portfolio_alerts:
            report += f"* {alert}\n"

    # Insight
    report += "\n---\n> **💡 소사냥꾼의 한 줄 평 (투자 인사이트)**\n"
    insight = get_hunter_insight(market_data)
    report += f"> \"{insight}\"\n"

    return report

def send_telegram_message(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("텔레그램 메시지 전송 성공!")
    except Exception as e:
        print(f"텔레그램 메시지 전송 실패: {e}\n응답: {response.text if 'response' in locals() else ''}")

def main():
    print("시장 데이터 수집 중...")
    market_data = get_market_data()
    
    print("보유/관심종목 데이터 수집 중...")
    portfolio_alerts, portfolio_news = get_portfolio_data()
    
    print("뉴스 및 보고서 수집 중...")
    news_data = {
        "매일경제 (MK) 헤드라인": get_rss_news("https://www.mk.co.kr/rss/30000001/", count=3),
        "한국경제 (Hankyung) 금융": get_rss_news("https://www.hankyung.com/feed/finance", count=3),
        "KED Global (한국 경제 글로벌)": get_rss_news("https://www.kedglobal.com/newsRss", count=3),
        "CNBC World News": get_rss_news("https://www.cnbc.com/id/100727362/device/rss/", count=3),
        
        "한경 컨센서스 (최신)": get_news("site:consensus.hankyung.com 기업 산업 시장 리포트", count=3),
        "KCMI 자본시장연구원": get_news("site:kcmi.re.kr 연구 보고서", count=3),
        
        "글로벌 경제 및 주요 이슈": get_news("미국 경제 지표 CPI PMI 고용 국채 금리 연준", count=3),
        "반도체 및 나스닥 테마": get_news("엔비디아 TSMC 삼성전자 하이닉스 반도체 규제 전망", count=3),
        "HBF 관련 뉴스": get_news("현대차 테슬라 인도 증시 전망", count=3),
        "포트폴리오 뉴스": get_news("배당주 금융주 자사주 소각 밸류업", count=3)
    }
    
    print("시장 심리 및 일정 수집 중...")
    fng_index = get_fear_greed_index()
    economic_events = get_economic_calendar()
    
    report_text = generate_markdown_report(market_data, news_data, portfolio_alerts, portfolio_news, fng_index, economic_events)
    
    # 터미널/로그 출력용 (인코딩 오류 방지)
    try:
        print("\n--- 생성된 리포트 ---\n")
        print(report_text)
    except UnicodeEncodeError:
        print("\n--- 생성된 리포트 (터미널에서 이모지 표시 불가) ---\n")
        print(report_text.encode('ascii', 'ignore').decode('ascii'))
    
    # 텔레그램 전송
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_chat_id:
        print("텔레그램으로 브리핑을 전송합니다...")
        send_telegram_message(telegram_token, telegram_chat_id, report_text)
    else:
        print("경고: TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 환경변수가 설정되지 않아 텔레그램 전송을 건너뜁니다.")

if __name__ == "__main__":
    main()
