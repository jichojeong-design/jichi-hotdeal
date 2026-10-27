import urllib.request
import re
import sys
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding='utf-8')

COMMON_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# 🧠 지치 아뜰리에 스마트 카테고리 판별 사전 (키워드 기반 교정)
FOOD_KEYWORDS = [
    '케찹', '케첩', '소스', '드레싱', '라면', '김치', '고기', '한우', '삼겹살', '만두', '피자', '치킨',
    '과자', '초코', '쿠키', '캔디', '음료', '커피', '원두', '우유', '치즈', '쌀', '햇반', '햇반', '생수',
    '탄산수', '사과', '배', '포도', '딸기', '과일', '오이', '나물', '간장', '고추장', '양념', '참치', '스팸',
    '밀키트', '국', '탕', '찌개', '전골', '샤브', '소시지', '핫도그', '빵', '베이커리', '유산균', '영양제', '비타민'
]

FASHION_KEYWORDS = [
    '팬츠', '바지', '청바지', '슬랙스', '트레이닝', '셔츠', '티셔츠', '맨투맨', '후드', '가디건', '니트',
    '자켓', '점퍼', '코트', '패딩', '다운', '조끼', '양말', '속옷', '팬티', '브라', '신발', '스니커즈',
    '운동화', '구두', '슬리퍼', '모자', '볼캡', '가방', '백팩', '벨트', '지갑', '의류', '패션'
]

LIVING_KEYWORDS = [
    '세제', '섬유유연제', '탈취제', '디퓨저', '휴지', '물티슈', '샴푸', '린스', '바디워시', '치약', '칫솔',
    '청소', '수세미', '냄비', '후라이팬', '그릇', '접시', '유리컵', '텀블러', '수건', '타월', '매트', '베개',
    '이불', '침구', '의자', '책상', '가구', '건전지', '멀티탭'
]

def determine_smart_category(title, origin_category):
    """
    작성자가 잘못 지정한 카테고리를 제목 키워드로 스마트하게 1차 교정
    """
    clean_t = title.lower()

    # 1. 식품 키워드 우선 검사 (케찹, 소스 등)
    if any(k in clean_t for k in FOOD_KEYWORDS):
        return '식품'

    # 2. 의류/패션 키워드 검사
    if any(k in clean_t for k in FASHION_KEYWORDS):
        return '의류'

    # 3. 생활용품 키워드 검사
    if any(k in clean_t for k in LIVING_KEYWORDS):
        return '생활'

    # 4. 키워드에 안 걸리면 작성자가 원래 지정한 카테고리 유지
    return origin_category if origin_category else '기타'

def clean_title_text(raw_text):
    t = re.sub(r'\[.*?\]', '', raw_text)
    t = re.sub(r'\(.*?\)', '', t)
    t = re.sub(r'(선착순특가|역대급특가|초특가|무료배송|토스쇼핑|지마켓|11번가|옥션).*', '', t)
    t = re.sub(r'[\+·｜]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

# 1. 이토랜드 수집
def fetch_etoland_deals(limit=25):
    url = 'https://www.etoland.co.kr/b/hotdeal'
    req = urllib.request.Request(url, headers=COMMON_HEADERS)
    deals = []
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            soup = BeautifulSoup(resp.read().decode('utf-8', errors='ignore'), 'html.parser')
            for a in soup.select('a[href^="/b/hotdeal/view/"]'):
                href = a.get('href', '')
                if '#' in href: continue
                li = a.find_parent('li')
                if not li: continue

                full_text = li.get_text(separator='|', strip=True)
                parts = [p.strip() for p in full_text.split('|') if p.strip()]
                if not parts or '공지' in parts or '핫딜 게시판 이용안내' in parts[0]:
                    continue

                time_str = ""
                for p in parts:
                    if '전' in p or '방금' in p or re.match(r'^\d{2}:\d{2}$', p):
                        time_str = p
                        break
                if not time_str: continue

                raw_title = parts[0]
                clean_name = clean_title_text(raw_title)
                if len(clean_name) < 2: continue

                community_url = f"https://www.etoland.co.kr{href}"
                if any(d['community_url'] == community_url for d in deals): continue

                source_mall = "일반"
                mall_type = "general"
                if '토스' in full_text: 
                    source_mall = "토스쇼핑"
                    mall_type = "toss"
                elif '네이버' in full_text: 
                    source_mall = "네이버"
                    mall_type = "naver"
                elif '지마켓' in full_text or 'G마켓' in full_text: 
                    source_mall = "G마켓"
                    mall_type = "gmarket"
                elif '11번가' in full_text: 
                    source_mall = "11번가"
                    mall_type = "11st"
                elif '쿠팡' in full_text: 
                    source_mall = "쿠팡"
                    mall_type = "coupang"
                elif '옥션' in full_text:
                    source_mall = "옥션"
                    mall_type = "auction"

                # 원본 카테고리 추출
                raw_category = "기타"
                for cat in ['식품', '의류', '생활', '디지털', '가전', '뷰티', '패션']:
                    if cat in parts:
                        raw_category = cat
                        break

                # ⭐ 스마트 카테고리 교정 엔진 가동 (케찹 등 오분류 완벽 해결)
                category = determine_smart_category(clean_name, raw_category)

                price = 0
                for p in parts:
                    m = re.match(r'^([0-9,]+)원$', p)
                    if m:
                        price = int(m.group(1).replace(',', ''))
                        break

                enc_q = urllib.parse.quote(clean_name)
                if mall_type == "gmarket":
                    direct_buy_url = f"https://browse.gmarket.co.kr/search?keyword={enc_q}"
                elif mall_type == "11st":
                    direct_buy_url = f"https://search.11st.co.kr/Search.tmall?kwd={enc_q}"
                elif mall_type == "auction":
                    direct_buy_url = f"https://browse.auction.co.kr/search?keyword={enc_q}"
                elif mall_type == "coupang":
                    direct_buy_url = f"https://www.coupang.com/np/search?component=&q={enc_q}"
                elif mall_type == "toss":
                    direct_buy_url = community_url
                elif mall_type == "naver":
                    direct_buy_url = f"https://search.shopping.naver.com/search/all?query={enc_q}"
                else:
                    direct_buy_url = f"https://search.shopping.naver.com/search/all?query={enc_q}"

                deals.append({
                    'community': '이토랜드',
                    'title': clean_name,
                    'category': category,
                    'source_mall': source_mall,
                    'is_toss': (source_mall == "토스쇼핑"),
                    'price': price,
                    'time': time_str,
                    'community_url': community_url,
                    'direct_buy_url': direct_buy_url
                })
                if len(deals) >= limit: break
    except Exception as e:
        print(f"❌ 이토랜드 수집 오류: {e}")
    return deals

# 2. 어미새 수집
def fetch_eomisae_deals(limit=15):
    deals = []
    targets = [
        ('/rt', '기타정보', '기타'),
        ('/fs', '패션정보', '패션')
    ]
    for path, sec_name, def_cat in targets:
        url = f"https://eomisae.co.kr{path}"
        req = urllib.request.Request(url, headers=COMMON_HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                soup = BeautifulSoup(resp.read().decode('utf-8', errors='ignore'), 'html.parser')
                for tr in soup.select('table tr'):
                    td_title = tr.select_one('td.title')
                    if not td_title or '공지' in tr.get_text():
                        continue
                    a = td_title.select_one('a')
                    if not a: continue
                    href = a.get('href', '')
                    if 'adlink' in href: continue
                    
                    raw_title = a.get_text(strip=True)
                    clean_name = clean_title_text(raw_title)
                    if len(clean_name) < 2: continue

                    community_url = f"https://eomisae.co.kr{href}" if href.startswith('/') else href
                    if any(d['community_url'] == community_url for d in deals): continue

                    price = 0
                    m = re.search(r'([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,7})\s*원?', raw_title)
                    if m:
                        price = int(m.group(1).replace(',', ''))

                    source_mall = "어미새픽"
                    if '네이버' in raw_title: source_mall = "네이버"
                    elif '무신사' in raw_title: source_mall = "무신사"
                    elif '지마켓' in raw_title: source_mall = "G마켓"

                    # 스마트 카테고리 교정
                    category = determine_smart_category(clean_name, def_cat)

                    enc_q = urllib.parse.quote(clean_name)
                    direct_buy_url = f"https://search.shopping.naver.com/search/all?query={enc_q}"

                    deals.append({
                        'community': '어미새',
                        'title': clean_name,
                        'category': category,
                        'source_mall': source_mall,
                        'is_toss': False,
                        'price': price,
                        'time': '오늘 실시간',
                        'community_url': community_url,
                        'direct_buy_url': direct_buy_url
                    })
                    if len(deals) >= limit: break
        except Exception as e:
            print(f"❌ 어미새 ({path}) 수집 오류: {e}")
    return deals

def get_all_hotdeals():
    return fetch_etoland_deals(limit=25) + fetch_eomisae_deals(limit=15)
