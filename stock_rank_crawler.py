"""네이버 증권(https://stock.naver.com/market/stock/kr) 메인의 '거래대금 상위' 랭킹 크롤러.

이 페이지는 자바스크립트로 화면을 그려서 requests로는 데이터가 비어 있다.
그래서 Selenium(헤드리스 Chrome)으로 화면을 완성시킨 뒤, 그 HTML을 BeautifulSoup4로 파싱한다.
브라우저에서 저장한 HTML 파일이 있다면 --html 옵션으로 브라우저 없이 파싱할 수도 있다.

랭킹 그룹 (data-nlogs 값 기준)
    rank.stkkrlist  국내주식      rank.stkuslist  해외주식
    rank.etfkrlist  국내 ETF      rank.cryptolist 가상자산

사용법:
    python stock_rank_crawler.py                    # 4개 그룹 모두 출력
    python stock_rank_crawler.py -g kr              # 국내주식만 (kr/us/etf/crypto)
    python stock_rank_crawler.py -x rank.xlsx       # 엑셀 저장
    python stock_rank_crawler.py -o rank.json       # JSON 저장
    python stock_rank_crawler.py --html page.html   # 저장된 HTML 파싱
필요 패키지: beautifulsoup4, selenium (엑셀 저장 시 openpyxl)
"""
import argparse
import json
import re

from bs4 import BeautifulSoup

URL = "https://stock.naver.com/market/stock/kr"
BASE = "https://stock.naver.com"

GROUPS = {  # data-nlogs 값 -> (옵션 이름, 화면 이름)
    "rank.stkkrlist": ("kr", "국내주식"),
    "rank.stkuslist": ("us", "해외주식"),
    "rank.etfkrlist": ("etf", "국내 ETF"),
    "rank.cryptolist": ("crypto", "가상자산"),
}


def render_html(timeout=20):
    """Selenium으로 자바스크립트가 실행된 뒤의 HTML을 가져온다."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait

    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1400,1000")
    opts.add_argument("--lang=ko-KR")
    driver = webdriver.Chrome(options=opts)
    try:
        driver.get(URL)
        try:
            WebDriverWait(driver, timeout).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[class*="GlobalStockRankingV2_stock-item__"]')))
        except TimeoutException:
            pass  # 랭킹 영역이 없으면 빈 결과가 되어 main()에서 안내 메시지를 출력
        return driver.page_source
    finally:
        driver.quit()


def read_html_file(path):
    """저장된 HTML 파일을 읽는다. 인코딩(UTF-8/UTF-8 BOM/CP949)을 차례로 시도."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        raise SystemExit(f"HTML 파일을 읽을 수 없습니다: {e}")
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def text_of(el, selector):
    """CSS 클래스는 빌드마다 뒤 해시(__xxxx)가 바뀌므로 앞부분만 부분 일치로 찾는다."""
    found = el.select_one(selector)
    return " ".join(found.get_text().split()) if found else ""


def parse_item(li):
    a = li.select_one("a[data-nlogs]")
    href = a["href"]

    price = text_of(li, '[class*="ModulePriceNumber_price__"]')
    prefix = text_of(li, '[class*="ModulePriceNumber_prefix__"]')      # 해외주식 '$'
    session = text_of(li, '[class*="HomeTopStockInfo_price-session__"]')  # 해외주식 'Pre' 등

    # 등락: 스크린리더용 '상승/하락' 텍스트(.a11y)를 방향으로, 나머지를 변동폭으로 사용
    change_el = li.select_one('[class*="ModulePriceChange_amount__"]')
    direction = text_of(change_el, ".a11y") if change_el else ""
    change = ""
    if change_el:
        for hidden in change_el.select(".a11y"):
            hidden.extract()
        change = " ".join(change_el.get_text().split())

    trading = li.select_one('[class*="HomeTopStockInfo_trading-value__"]')
    if trading:
        for label in trading.select('[class*="HomeTopStockInfo_label__"]'):
            label.extract()
    rate = text_of(li, '[class*="ModulePercent_module-percent__"]').strip("()")
    sign = {"상승": "+", "하락": "-"}.get(direction, "")

    return {
        "rank": int(text_of(li, '[class*="HomeTopStockInfo_rank-number__"]') or 0),
        "name": text_of(li, '[class*="StockDoubleLineText_text__"]'),
        "code": href.rstrip("/").split("/")[-2] if href.endswith("/price") else href.split("/")[-1],
        "price": prefix + price,
        "session": session,
        "direction": direction,
        "change": (sign + change) if change and not change.startswith(("+", "-")) else change,
        "rate": rate,
        "trading_value": " ".join(trading.get_text().split()) if trading else "",
        "url": BASE + href,
    }


def parse_rankings(html):
    """HTML에서 그룹별 랭킹을 추출. {그룹키: [종목 dict, ...]}"""
    soup = BeautifulSoup(html, "html.parser")
    result = {}
    for link in soup.select('a[data-nlogs^="rank."]'):
        key = link["data-nlogs"]
        if key not in GROUPS:
            continue
        li = link.find_parent("li")
        # 각 그룹에는 무한 스크롤용 복제본 <ol aria-hidden="true">가 있으므로 제외
        if li is None or li.find_parent("ol", attrs={"aria-hidden": "true"}):
            continue
        try:
            result.setdefault(key, []).append(parse_item(li))
        except (AttributeError, KeyError, ValueError, TypeError):
            continue  # 구조가 다른 항목 하나 때문에 전체가 중단되지 않도록 건너뜀
    return result


def print_rankings(data):
    for key, (_, title) in GROUPS.items():
        items = data.get(key)
        if not items:
            continue
        print(f"\n[{title}] 거래대금 상위")
        for it in items:
            sess = f"[{it['session']}] " if it["session"] else ""
            print(f"  {it['rank']:>2}. {it['name']:<16} {sess}{it['price']:>12}  "
                  f"{it['direction']} {it['change']:>8} ({it['rate']})  거래대금 {it['trading_value']}")


def save_excel(data, path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    headers = [("순위", "rank", 6), ("종목명", "name", 24), ("코드", "code", 12),
               ("현재가", "price", 14), ("구분", "session", 8), ("등락", "direction", 8),
               ("변동", "change", 12), ("등락률", "rate", 10),
               ("거래대금", "trading_value", 16), ("링크", "url", 50)]
    wb = Workbook()
    wb.remove(wb.active)
    for key, (_, title) in GROUPS.items():
        if key not in data:
            continue
        ws = wb.create_sheet(title)
        ws.append([h for h, _, _ in headers])
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="2F5597")
            c.alignment = Alignment(horizontal="center")
        for it in data[key]:
            ws.append([it[k] for _, k, _ in headers])
            link = ws.cell(row=ws.max_row, column=len(headers))
            link.hyperlink = link.value
            link.font = Font(color="0563C1", underline="single")
        for i, (_, _, w) in enumerate(headers, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A2"
    wb.save(path)


def main():
    parser = argparse.ArgumentParser(description="네이버 증권 거래대금 상위 랭킹 크롤러")
    parser.add_argument("-g", "--group", choices=[v[0] for v in GROUPS.values()],
                        help="특정 그룹만 (kr/us/etf/crypto)")
    parser.add_argument("--html", help="브라우저 없이, 저장된 HTML 파일을 파싱")
    parser.add_argument("-o", "--output", help="JSON 저장 경로")
    parser.add_argument("-x", "--excel", help="엑셀(.xlsx) 저장 경로")
    args = parser.parse_args()

    if args.html:
        html = read_html_file(args.html)
    else:
        try:
            html = render_html()
        except Exception as e:
            # Selenium 예외는 메시지가 비어 있고 스택트레이스만 붙는 경우가 많아 종류와 첫 줄만 보여준다
            reason = (str(e).strip().splitlines() or [""])[0] or "브라우저/드라이버 실행 오류"
            raise SystemExit(
                f"페이지를 불러오지 못했습니다: {type(e).__name__}: {reason}\n"
                "Chrome이 설치되어 있는지, 인터넷에 연결되어 있는지 확인하거나 --html 옵션을 사용하세요.")

    data = parse_rankings(html)
    if args.group:
        data = {k: v for k, v in data.items() if GROUPS[k][0] == args.group}
    if not data:
        raise SystemExit(
            "랭킹 데이터(GlobalStockRankingV2)를 찾지 못했습니다.\n"
            "자동 접속한 화면에는 이 영역이 없을 수 있습니다. 브라우저에서 랭킹이 보이는 화면을 열고\n"
            "개발자도구(F12) > Elements > <html> 우클릭 > Copy > Copy outerHTML 로 HTML을 파일에 저장한 뒤\n"
            "  python stock_rank_crawler.py --html 저장한파일.html\n"
            "로 실행하세요.")

    print_rankings(data)
    try:
        if args.output:
            named = {GROUPS[k][1]: v for k, v in data.items()}
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(named, f, ensure_ascii=False, indent=2)
            print(f"\nJSON 저장: {args.output}")
        if args.excel:
            save_excel(data, args.excel)
            print(f"엑셀 저장: {args.excel}")
    except PermissionError:
        raise SystemExit("저장 실패: 파일에 쓸 수 없습니다. 같은 이름의 파일이 열려 있다면 닫고 다시 시도하세요.")
    except OSError as e:
        raise SystemExit(f"저장 실패: {e}")


if __name__ == "__main__":
    main()
