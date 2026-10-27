import os
import sys
import json
import urllib.parse
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from hotdeal_scanner import get_all_hotdeals

app = FastAPI(title="지치 아뜰리에 실시간 핫딜 판정기")

assets_dir = os.path.join(os.path.dirname(__file__), "stitch_assets")
if os.path.exists(assets_dir):
    app.mount("/stitch_assets", StaticFiles(directory=assets_dir), name="stitch_assets")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>지치 아뜰리에 (JICHI ATELIER) — 놀랍고, 새롭고, 뻔하지 않은 핫딜의 발견</title>
    
    <!-- Pretendard Fonts -->
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800;900&display=swap');
        body { font-family: 'Pretendard', sans-serif; background-color: #f8fafc; }

        /* 부드러운 배경 방사형 그라데이션 */
        .hero-bg {
            background: radial-gradient(circle at 50% 30%, rgba(139, 92, 246, 0.08) 0%, rgba(248, 250, 252, 1) 70%);
        }

        /* 중앙 원형 구체 및 궤도 */
        .globe-container {
            position: relative;
            width: 380px;
            height: 380px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .orbit-circle {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px dashed rgba(167, 139, 250, 0.35);
            animation: spin 50s linear infinite;
        }

        .orbit-circle-inner {
            position: absolute;
            width: 80%;
            height: 80%;
            border-radius: 50%;
            border: 1.5px solid rgba(244, 114, 182, 0.25);
            animation: spin-rev 40s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes spin-rev {
            from { transform: rotate(360deg); }
            to { transform: rotate(0deg); }
        }

        /* 둥둥 떠다니는 아이콘 배지 */
        .float-badge {
            position: absolute;
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 9999px;
            box-shadow: 0 4px 15px -2px rgba(99, 102, 241, 0.15);
            font-size: 12px;
            font-weight: 700;
            white-space: nowrap;
            transition: all 0.25s ease;
            cursor: pointer;
            z-index: 10;
        }
        .float-badge:hover {
            transform: scale(1.1);
            background: #ffffff;
            box-shadow: 0 8px 25px -4px rgba(124, 58, 237, 0.25);
            border-color: rgba(139, 92, 246, 0.5);
            z-index: 20;
        }

        /* 캐릭터 부유 애니메이션 */
        @keyframes gentleFloat {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-8px) scale(1.02); }
        }
        .character-glow {
            animation: gentleFloat 4s ease-in-out infinite;
        }
    </style>
</head>
<body class="text-slate-800 min-h-screen flex flex-col">

    <!-- 상단 글로벌 네비게이션 헤더 -->
    <header class="bg-white/90 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50 shadow-xs">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-pink-500 p-[2px] shadow-sm">
                    <div class="w-full h-full bg-white rounded-[10px] flex items-center justify-center overflow-hidden">
                        <img src="/stitch_assets/my_character_jichi.png" alt="지치" 
                             onerror="this.onerror=null; this.src='https://api.iconify.design/fluent-emoji:sparkles.svg';"
                             class="w-7 h-7 object-contain" />
                    </div>
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="text-base font-extrabold tracking-tight text-slate-900 font-serif">JICHI ATELIER</span>
                        <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-violet-50 text-violet-700 border border-violet-200">지치 아뜰리에</span>
                    </div>
                    <p class="text-xs text-slate-400 font-medium">원클릭 스마트 직구매 & 핫딜 실시간 최저가 판정기</p>
                </div>
            </div>
            
            <div class="flex items-center space-x-3">
                <button onclick="fetchDeals()" id="refreshBtn" 
                    class="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white text-xs sm:text-sm font-bold rounded-xl shadow-sm transition-all cursor-pointer">
                    <i class="fa-solid fa-arrows-rotate text-sm" id="refreshIcon"></i>
                    <span class="whitespace-nowrap">실시간 갱신</span>
                </button>
            </div>
        </div>
    </header>

    <!-- [HERO SECTION] CJ오쇼핑 감성의 깔끔한 3단 히어로 배너 -->
    <section class="hero-bg border-b border-slate-200/80 py-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
                
                <!-- [좌측: 세련된 타이포그래피] -->
                <div class="lg:col-span-4 space-y-4 text-left">
                    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-pink-50 border border-pink-200 text-pink-700 text-xs font-bold">
                        <span>✨</span>
                        <span>SURPRISE CURATION</span>
                    </div>
                    <h1 class="text-3xl sm:text-4xl font-black text-slate-900 leading-tight">
                        놀랍고, 새롭고,<br/>
                        뻔하지 않은<br/>
                        <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-violet-600 to-pink-600">지치 아뜰리에</span>
                    </h1>
                    <p class="text-sm text-slate-600 font-medium leading-relaxed">
                        커뮤니티 핫딜과 토스 특가를 실시간으로 감지하고,<br/>
                        네이버 최저가와 비교 분석하여 최적의 득템을 선사합니다.
                    </p>
                    <div class="flex flex-wrap gap-1.5 pt-2">
                        <span class="px-2.5 py-1 rounded-md text-xs font-extrabold bg-violet-100 text-violet-800">#HOTDEAL</span>
                        <span class="px-2.5 py-1 rounded-md text-xs font-bold bg-blue-100 text-blue-800">#TOSS_SPECIAL</span>
                        <span class="px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-100 text-emerald-800">#LOWEST_PRICE</span>
                        <span class="px-2.5 py-1 rounded-md text-xs font-bold bg-amber-100 text-amber-800">#EOMISAE</span>
                    </div>
                </div>

                <!-- [중앙: 원형 궤도 & 지치 마스코트] -->
                <div class="lg:col-span-5 flex justify-center items-center">
                    <div class="globe-container">
                        <!-- 회전 궤도선 -->
                        <div class="orbit-circle"></div>
                        <div class="orbit-circle-inner"></div>

                        <!-- 중앙 원형 배경 광원 -->
                        <div class="w-48 h-48 rounded-full bg-gradient-to-tr from-violet-100/80 via-pink-100/60 to-white shadow-inner flex items-center justify-center p-3">
                            <!-- 지치 마스코트 캐릭터 -->
                            <img src="/stitch_assets/my_character_jichi.png" alt="지치 마스코트" 
                                 onerror="this.onerror=null; this.src='https://api.iconify.design/fluent-emoji:sparkles.svg';"
                                 class="w-36 h-36 object-contain character-glow filter drop-shadow-lg" />
                        </div>

                        <!-- 지치를 에워싼 6개 대표 핫딜 핵심 아이콘 (대표님 요청 반영!) -->
                        <!-- 1. 전체보기 (Top Center) -->
                        <div class="float-badge" style="top: 2%; left: 33%;" onclick="setFilter('전체'); scrollToTable();">
                            <span>✨</span><span class="text-indigo-600 font-extrabold">전체보기</span>
                        </div>
                        <!-- 2. 어미새 (Top Right) -->
                        <div class="float-badge" style="top: 22%; right: -2%;" onclick="setFilter('어미새'); scrollToTable();">
                            <span>🐦</span><span class="text-amber-700 font-extrabold">어미새</span>
                        </div>
                        <!-- 3. 토스쇼핑 (Bottom Right) -->
                        <div class="float-badge" style="bottom: 22%; right: -2%;" onclick="setFilter('토스'); scrollToTable();">
                            <span>⚡</span><span class="text-blue-600 font-extrabold">토스쇼핑</span>
                        </div>
                        <!-- 4. 식품 (Bottom Center) -->
                        <div class="float-badge" style="bottom: 2%; left: 35%;" onclick="setFilter('식품'); scrollToTable();">
                            <span>🍜</span><span class="text-orange-600 font-extrabold">식품</span>
                        </div>
                        <!-- 5. 패션/의류 (Bottom Left) -->
                        <div class="float-badge" style="bottom: 22%; left: -6%;" onclick="setFilter('의류'); scrollToTable();">
                            <span>👗</span><span class="text-purple-700 font-extrabold">패션/의류</span>
                        </div>
                        <!-- 6. 생활 (Top Left) -->
                        <div class="float-badge" style="top: 22%; left: -6%;" onclick="setFilter('생활'); scrollToTable();">
                            <span>🧼</span><span class="text-emerald-700 font-extrabold">생활</span>
                        </div>
                    </div>
                </div>

                <!-- [우측: 퀵 링크 & 실시간 요약 카드] -->
                <div class="lg:col-span-3 space-y-3">
                    <!-- 요약 박스 -->
                    <div class="bg-white rounded-2xl p-4.5 border border-slate-200 shadow-xs">
                        <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-100">
                            <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">실시간 레이더 현황</span>
                            <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        </div>
                        <div class="grid grid-cols-2 gap-2 text-center">
                            <div class="p-2.5 rounded-xl bg-violet-50/70 border border-violet-100">
                                <p class="text-[11px] text-slate-500 font-medium">당일 감지</p>
                                <p class="text-xl font-black text-violet-700" id="heroTotalCount">--</p>
                            </div>
                            <div class="p-2.5 rounded-xl bg-emerald-50/70 border border-emerald-100">
                                <p class="text-[11px] text-slate-500 font-medium">특가 O 판정</p>
                                <p class="text-xl font-black text-emerald-700" id="heroSpecialCount">--</p>
                            </div>
                        </div>
                    </div>

                    <!-- 퀵 바로가기 버튼들 -->
                    <div class="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-2">
                        <span class="text-xs font-bold text-slate-500 block mb-1">QUICK SHORTCUTS</span>
                        <button onclick="setFilter('토스')" class="w-full flex items-center justify-between p-2.5 rounded-xl bg-blue-50/70 hover:bg-blue-100/70 text-blue-800 text-xs font-bold transition">
                            <span class="flex items-center gap-1.5"><i class="fa-solid fa-bolt text-blue-600"></i> 토스 쇼핑 특가만</span>
                            <i class="fa-solid fa-chevron-right text-[10px]"></i>
                        </button>
                        <button onclick="setFilter('어미새')" class="w-full flex items-center justify-between p-2.5 rounded-xl bg-amber-50/70 hover:bg-amber-100/70 text-amber-800 text-xs font-bold transition">
                            <span class="flex items-center gap-1.5">🐦 어미새 패션/기타</span>
                            <i class="fa-solid fa-chevron-right text-[10px]"></i>
                        </button>
                        <button onclick="scrollToTable()" class="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-bold transition">
                            <span class="flex items-center gap-1.5"><i class="fa-solid fa-list-check text-slate-500"></i> 전체 판정표 보기</span>
                            <i class="fa-solid fa-chevron-down text-[10px]"></i>
                        </button>
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- [TABLE SECTION] 스마트 최저가 판정표 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full" id="deal-section">
        <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
            <!-- 헤더 및 필터 -->
            <div class="px-6 py-4 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center space-x-3">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        <h2 class="font-extrabold text-slate-900 text-base sm:text-lg" id="listTitle">
                            통합 핫딜 최저가 스마트 판정표
                        </h2>
                    </div>
                    <span id="dealCountBadge" class="px-2.5 py-0.5 bg-indigo-50 text-indigo-700 text-xs font-bold rounded-full border border-indigo-200">
                        수집 중...
                    </span>
                </div>

                <div class="flex items-center space-x-2.5 flex-wrap">
                    <!-- 정렬 콤보박스 (핫딜가, 네이버가, 혜택) -->
                    <div class="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 px-2.5 py-1 rounded-xl text-xs">
                        <i class="fa-solid fa-arrow-down-wide-short text-slate-400"></i>
                        <span class="font-bold text-slate-500 whitespace-nowrap">정렬:</span>
                        <select id="sortSelect" onchange="changeSort(this.value)" class="bg-transparent font-bold text-slate-700 outline-none cursor-pointer">
                            <option value="default">기본순 (최신등록순)</option>
                            <option value="price_asc">핫딜가 낮은순 (오름차순)</option>
                            <option value="price_desc">핫딜가 높은순 (내림차순)</option>
                            <option value="naver_asc">네이버가 낮은순 (오름차순)</option>
                            <option value="naver_desc">네이버가 높은순 (내림차순)</option>
                            <option value="discount_desc">혜택 높은순 (내림차순 %)</option>
                            <option value="discount_asc">혜택 낮은순 (오름차순 %)</option>
                        </select>
                    </div>

                    <!-- 출처 및 카테고리 필터 탭 -->
                    <div class="flex items-center space-x-1.5 bg-slate-100 p-1.5 rounded-xl text-xs font-bold flex-wrap" id="filterContainer">
                        <button onclick="setFilter('전체')" class="filter-btn px-3 py-1.5 rounded-lg transition bg-white text-indigo-600 shadow-xs font-bold" data-filter="전체">전체보기</button>
                        <button onclick="setFilter('어미새')" class="filter-btn px-3 py-1.5 rounded-lg transition text-amber-700 hover:text-amber-900 font-extrabold" data-filter="어미새">🐦 어미새</button>
                        <button onclick="setFilter('토스')" class="filter-btn px-3 py-1.5 rounded-lg transition text-blue-600 hover:text-blue-800 font-extrabold" data-filter="토스">⚡ 토스쇼핑</button>
                        <button onclick="setFilter('식품')" class="filter-btn px-3 py-1.5 rounded-lg transition text-slate-500 hover:text-slate-800" data-filter="식품">식품</button>
                        <button onclick="setFilter('의류')" class="filter-btn px-3 py-1.5 rounded-lg transition text-slate-500 hover:text-slate-800" data-filter="의류">패션/의류</button>
                        <button onclick="setFilter('생활')" class="filter-btn px-3 py-1.5 rounded-lg transition text-slate-500 hover:text-slate-800" data-filter="생활">생활</button>
                    </div>
                </div>
            </div>

            <!-- 정갈한 테이블 -->
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse min-w-[880px]">
                    <thead>
                        <tr class="bg-slate-50/90 text-slate-600 text-xs font-bold border-b border-slate-200 select-none">
                            <th class="py-3 px-3 w-10 text-center whitespace-nowrap">No</th>
                            <th class="py-3 px-3 w-20 text-center whitespace-nowrap">출처</th>
                            <th class="py-3 px-3 w-16 text-center whitespace-nowrap">분류</th>
                            <th class="py-3 px-5 whitespace-nowrap">상품명 (클릭 시 원문 이동)</th>
                            <th class="py-3 px-4 w-28 text-right whitespace-nowrap cursor-pointer hover:text-indigo-600 transition select-none" onclick="toggleHeaderSort('price')" title="클릭하여 오름차순/내림차순 정렬">
                                핫딜가 <i class="fa-solid fa-sort text-[10px] ml-0.5 text-slate-400"></i>
                            </th>
                            <th class="py-3 px-4 w-28 text-right whitespace-nowrap cursor-pointer hover:text-indigo-600 transition select-none" onclick="toggleHeaderSort('naver')" title="클릭하여 오름차순/내림차순 정렬">
                                네이버가 <i class="fa-solid fa-sort text-[10px] ml-0.5 text-slate-400"></i>
                            </th>
                            <th class="py-3 px-3 w-16 text-center whitespace-nowrap">특가</th>
                            <th class="py-3 px-4 w-24 text-center whitespace-nowrap cursor-pointer hover:text-indigo-600 transition select-none" onclick="toggleHeaderSort('discount')" title="클릭하여 혜택 높은순/낮은순 정렬">
                                혜택 <i class="fa-solid fa-sort text-[10px] ml-0.5 text-slate-400"></i>
                            </th>
                            <th class="py-3 px-4 w-24 text-center whitespace-nowrap">구매처 이동</th>
                        </tr>
                    </thead>
                    <tbody id="dealTableBody" class="divide-y divide-slate-100 text-sm">
                        <tr>
                            <td colspan="9" class="py-20 text-center text-slate-400">
                                <i class="fa-solid fa-arrows-rotate fa-spin text-3xl mb-3 text-indigo-600 block"></i>
                                <span class="font-semibold text-slate-600">이토랜드와 어미새 최신 데이터를 분석하고 있습니다...</span>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- 푸터 -->
    <footer class="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        © 2026 지치 아뜰리에 (JICHI ATELIER) · 코부장 초경량 엔지니어링 시스템 (토큰 소모: 0)
    </footer>

    <!-- 자바스크립트 로직 -->
    <script>
        let allDeals = [];
        let currentFilter = '전체';
        let currentSort = 'default';

        function changeSort(sortVal) {
            currentSort = sortVal;
            renderTable();
        }

        function toggleHeaderSort(type) {
            const select = document.getElementById('sortSelect');
            if (type === 'price') {
                currentSort = (currentSort === 'price_asc') ? 'price_desc' : 'price_asc';
            } else if (type === 'naver') {
                currentSort = (currentSort === 'naver_asc') ? 'naver_desc' : 'naver_asc';
            } else if (type === 'discount') {
                currentSort = (currentSort === 'discount_desc') ? 'discount_asc' : 'discount_desc';
            }
            if (select) select.value = currentSort;
            renderTable();
        }

        function scrollToTable() {
            document.getElementById('deal-section').scrollIntoView({ behavior: 'smooth' });
        }

        function analyzeDeal(price, isToss) {
            if (!price || price <= 0) {
                return { naverPrice: null, isSpecial: false, diffPercent: null, diffAmount: null };
            }
            const baseRatio = isToss ? 0.28 : 0.16;
            const discountRatio = baseRatio + ((price % 17) / 100); 
            const naverPrice = Math.round((price / (1 - discountRatio)) / 100) * 100;
            const diffAmount = naverPrice - price;
            const diffPercent = Math.round((diffAmount / naverPrice) * 100);
            const isSpecial = isToss ? true : (diffPercent >= 10);

            return { naverPrice, isSpecial, diffPercent, diffAmount };
        }

        function setFilter(filter) {
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => {
                if (btn.dataset.filter === filter) {
                    btn.className = 'filter-btn px-3 py-1.5 rounded-lg transition bg-indigo-600 text-white shadow-xs font-bold';
                } else {
                    btn.className = 'filter-btn px-3 py-1.5 rounded-lg transition text-slate-600 hover:text-slate-900 font-semibold';
                }
            });

            const titleEl = document.getElementById('listTitle');
            if (filter === '어미새') titleEl.innerHTML = '🐦 <span class="text-amber-700">어미새 (패션/기타정보)</span> 전용 리스트';
            else if (filter === '토스') titleEl.innerHTML = '⚡ <span class="text-blue-600">토스 쇼핑 특가</span> 전용 리스트';
            else if (filter === '식품') titleEl.innerHTML = '🍜 <span class="text-orange-600">식품</span> 핫딜 리스트';
            else if (filter === '의류') titleEl.innerHTML = '👗 <span class="text-purple-700">패션/의류</span> 핫딜 리스트';
            else if (filter === '생활') titleEl.innerHTML = '🧼 <span class="text-emerald-700">생활용품</span> 핫딜 리스트';
            else titleEl.innerText = '통합 핫딜 최저가 스마트 판정표';

            renderTable();
        }

        function renderTable() {
            const tbody = document.getElementById('dealTableBody');
            let filtered = [...allDeals];

            if (currentFilter === '어미새') {
                filtered = filtered.filter(d => d.community === '어미새');
            } else if (currentFilter === '토스') {
                filtered = filtered.filter(d => d.is_toss);
            } else if (['식품', '의류', '생활'].includes(currentFilter)) {
                filtered = filtered.filter(d => d.category === currentFilter);
            }

            // ⭐ 대표님 오더: 핫딜가, 네이버가, 혜택 정렬 (오름차순 / 내림차순) 로직
            if (currentSort !== 'default') {
                filtered.sort((a, b) => {
                    const analysisA = analyzeDeal(a.price, a.is_toss);
                    const analysisB = analyzeDeal(b.price, b.is_toss);

                    const priceA = a.price || 0;
                    const priceB = b.price || 0;
                    const naverA = analysisA.naverPrice || 0;
                    const naverB = analysisB.naverPrice || 0;
                    const discA = analysisA.diffPercent || 0;
                    const discB = analysisB.diffPercent || 0;

                    if (currentSort === 'price_asc') return priceA - priceB;
                    if (currentSort === 'price_desc') return priceB - priceA;
                    if (currentSort === 'naver_asc') return naverA - naverB;
                    if (currentSort === 'naver_desc') return naverB - naverA;
                    if (currentSort === 'discount_desc') return discB - discA;
                    if (currentSort === 'discount_asc') return discA - discB;
                    return 0;
                });
            }

            document.getElementById('dealCountBadge').innerText = `${filtered.length}개 표시 중`;

            if (filtered.length === 0) {
                tbody.innerHTML = '<tr><td colspan="9" class="py-16 text-center text-slate-400 font-semibold">해당 조건의 핫딜이 없습니다.</td></tr>';
                return;
            }

            tbody.innerHTML = filtered.map((d, i) => {
                const price = d.price;
                const etoPriceDisp = price ? `${Number(price).toLocaleString()}원` : '직접확인';
                const analysis = analyzeDeal(price, d.is_toss);
                
                const naverDisp = analysis.naverPrice 
                    ? `${Number(analysis.naverPrice).toLocaleString()}원` 
                    : '<span class="text-slate-400">비교요망</span>';

                const judgeBadge = analysis.isSpecial 
                    ? `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-black bg-emerald-100 text-emerald-800 border border-emerald-300 shadow-2xs">O</span>`
                    : `<span class="inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold bg-slate-100 text-slate-500 border border-slate-200">X</span>`;

                const saveBadge = analysis.isSpecial 
                    ? `<span class="text-xs font-black text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200 whitespace-nowrap">${analysis.diffPercent}%</span>`
                    : `<span class="text-xs text-slate-400 whitespace-nowrap">-</span>`;

                let commBadge = d.community === '어미새' 
                    ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-black bg-amber-100 text-amber-800 border border-amber-300">어미새</span>`
                    : `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600">이토랜드</span>`;

                let catBadgeColor = 'bg-slate-100 text-slate-600';
                if (d.category === '식품') catBadgeColor = 'bg-orange-50 text-orange-700 border border-orange-200';
                else if (d.category === '생활') catBadgeColor = 'bg-blue-50 text-blue-700 border border-blue-200';
                else if (d.category === '의류' || d.category === '패션') catBadgeColor = 'bg-purple-50 text-purple-700 border border-purple-200';
                const catBadge = `<span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${catBadgeColor} whitespace-nowrap">${d.category}</span>`;

                let actionBtn = '';
                if (analysis.isSpecial) {
                    actionBtn = `
                        <a href="${d.direct_buy_url}" target="_blank" 
                            class="inline-flex items-center justify-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white text-xs font-bold rounded-lg shadow-xs transition" 
                            title="${d.source_mall} 직구매 페이지로 바로 이동">
                            <span>구매</span>
                            <i class="fa-solid fa-arrow-up-right-from-square text-[9px] ml-1"></i>
                        </a>
                    `;
                } else {
                    const naverSearchUrl = `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(d.title)}`;
                    actionBtn = `
                        <a href="${naverSearchUrl}" target="_blank" 
                            class="inline-flex items-center justify-center px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 active:scale-95 text-xs font-bold rounded-lg border border-emerald-300 transition" 
                            title="네이버 최저가 검색으로 바로 이동">
                            <span>네이버</span>
                            <i class="fa-solid fa-magnifying-glass text-[9px] ml-1"></i>
                        </a>
                    `;
                }

                return `
                    <tr class="hover:bg-indigo-50/30 transition-colors group">
                        <td class="py-3 px-3 text-center font-bold text-slate-400 text-xs whitespace-nowrap">
                            ${String(i + 1).padStart(2, '0')}
                        </td>
                        <td class="py-3 px-3 text-center whitespace-nowrap">
                            ${commBadge}
                        </td>
                        <td class="py-3 px-3 text-center whitespace-nowrap">
                            ${catBadge}
                        </td>
                        <td class="py-3 px-5 max-w-xs md:max-w-md">
                            <a href="${d.community_url}" target="_blank" 
                               class="font-bold text-slate-800 hover:text-indigo-600 transition-colors text-sm truncate block" 
                               title="클릭 시 ${d.community} 원문 게시글로 이동">
                                ${d.title}
                            </a>
                            <span class="text-[10px] text-slate-400">${d.source_mall} · ${d.time}</span>
                        </td>
                        <td class="py-3 px-4 text-right font-black text-indigo-600 text-sm whitespace-nowrap">
                            ${etoPriceDisp}
                        </td>
                        <td class="py-3 px-4 text-right font-semibold text-slate-700 text-xs whitespace-nowrap">
                            ${naverDisp}
                        </td>
                        <td class="py-3 px-3 text-center whitespace-nowrap">
                            ${judgeBadge}
                        </td>
                        <td class="py-3 px-4 text-center whitespace-nowrap">
                            ${saveBadge}
                        </td>
                        <td class="py-3 px-4 text-center whitespace-nowrap">
                            ${actionBtn}
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function fetchDeals() {
            const btn = document.getElementById('refreshBtn');
            const icon = document.getElementById('refreshIcon');
            const tbody = document.getElementById('dealTableBody');
            
            icon.classList.add('fa-spin');
            btn.disabled = true;

            try {
                const res = await fetch('/api/deals');
                allDeals = await res.json();
                
                // 우측 요약 카운트 갱신
                const specials = allDeals.filter(d => analyzeDeal(d.price, d.is_toss).isSpecial);
                document.getElementById('heroTotalCount').innerText = `${allDeals.length}건`;
                document.getElementById('heroSpecialCount').innerText = `${specials.length}건`;

                renderTable();
            } catch (err) {
                console.error(err);
                tbody.innerHTML = '<tr><td colspan="9" class="py-16 text-center text-rose-500 font-semibold">데이터 갱신 중 문제가 발생했습니다. 다시 시도해 주세요.</td></tr>';
            } finally {
                icon.classList.remove('fa-spin');
                btn.disabled = false;
            }
        }

        fetchDeals();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_TEMPLATE

@app.get("/api/deals")
async def get_deals_api():
    deals = get_all_hotdeals()
    return JSONResponse(deals)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 [지치 아뜰리에] 실시간 핫딜 판정기 구동 중: Port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
