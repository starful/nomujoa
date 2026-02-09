// app/static/js/main.js

// 전역 변수 (HTML에서 주입됨)
const KPOP_DATA = window.GROUP_DATA || {};
let selectedGroup = "General";
let selectedMember = "All";
let currentOptions = []; // 현재 AI 번역 결과 옵션을 저장

// [개선] 페이지의 모든 리소스(폰트 포함)가 로드된 후 캔버스를 다시 렌더링
window.addEventListener('load', function() {
    document.fonts.ready.then(function () {
        console.log('Fonts are fully loaded.');
        if(typeof canvas !== 'undefined' && canvas) {
            canvas.requestRenderAll();
        }
    });
});

// 초기화
document.addEventListener("DOMContentLoaded", () => {
    updateUI(); // 다국어 텍스트 및 추천 문구 설정

    // 키보드 이벤트 (삭제)
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                const activeObj = canvas && canvas.getActiveObject();
                if (activeObj && !activeObj.isEditing) { 
                    canvas.remove(activeObj);
                    canvas.requestRenderAll();
                }
            }
        }
    });
});

/**
 * [UI 업데이트 함수]
 * 언어 설정에 맞춰 UI 텍스트와 추천 문구를 업데이트합니다.
 */
function updateUI() {
    const langSelect = document.getElementById('src-lang');
    if (!langSelect) return; 
    
    const selectedLang = langSelect.value;

    // 1. 입력창 Placeholder 변경
    const inputField = document.getElementById('jp-input');
    const placeholders = {
        "ja": "例: 大好き、結婚して",
        "en": "e.g., I love you, Marry me",
        "ko": "예: 사랑해, 완전 멋져",
        "zh": "例如：我爱你, 请和我结婚"
    };
    if (inputField && placeholders[selectedLang]) {
        inputField.placeholder = placeholders[selectedLang];
    }

    // 2. 추천 문구 렌더링
    renderQuickPhrases(selectedLang);

    // 3. UI 텍스트 번역 적용
    applyTranslations(selectedLang);
}

/**
 * UI 텍스트 번역 적용 함수
 */
function applyTranslations(lang) {
    // window.uiTranslations는 data.js에 정의되어 있다고 가정
    const t = (window.uiTranslations && window.uiTranslations[lang]) || (window.uiTranslations && window.uiTranslations['en']) || {};

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el && text) el.innerHTML = text;
    }

    setText("t-desc", t.desc);
    setText("t-label-group", t.label_group);
    setText("t-label-member", t.label_member);
    setText("t-label-quick", t.label_quick);
    setText("t-label-msg", t.label_msg);
    setText("t-btn-gen", t.btn_gen);
    
    setText("t-label-result", t.label_result);
    setText("t-txt-result-desc", t.txt_result_desc);
    setText("t-btn-retry", t.btn_retry);
    
    setText("t-label-bg", t.label_bg);
    setText("t-label-tpl", t.label_tpl);
    setText("t-label-stk", t.label_stk);
    
    setText("t-btn-save", t.btn_save);
    setText("t-btn-back-list", t.btn_back_list);
    setText("t-txt-save-desc", t.txt_save_desc);
    
    const resetBtns = document.querySelectorAll('.reset-link');
    resetBtns.forEach(btn => { if(t.btn_reset) btn.innerText = t.btn_reset; });

    if (t.seo_title) document.title = t.seo_title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && t.seo_desc) metaDesc.setAttribute("content", t.seo_desc);
    
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogTitle && t.seo_title) ogTitle.setAttribute("content", t.seo_title);
    if (ogDesc && t.seo_desc) ogDesc.setAttribute("content", t.seo_desc);
}

/**
 * 추천 문구 렌더링 함수
 */
function renderQuickPhrases(lang) {
    const container = document.getElementById("quick-phrase-container");
    if (!container) return;
    container.innerHTML = "";
    
    // window.quickPhrasesData는 data.js에 정의되어 있다고 가정
    const phrases = (window.quickPhrasesData && (window.quickPhrasesData[lang] || window.quickPhrasesData['en'])) || [];

    phrases.forEach(phrase => {
        const displayPhrase = phrase; 
        const inputPhrase = phrase.split(' (')[0]; 

        const btn = document.createElement("div");
        btn.className = "phrase-chip";
        btn.innerText = displayPhrase;
        btn.onclick = () => {
            const inputField = document.getElementById("jp-input");
            if(inputField) inputField.value = inputPhrase;
            
            const langSelect = document.getElementById('src-lang');
            if(langSelect) langSelect.value = lang;
            
            translateAndStart();
        };
        container.appendChild(btn);
    });
}

/**
 * 멤버 목록 업데이트 (HTML에서 onchange로 호출됨)
 */
function updateMembers() {
    const groupSelect = document.getElementById("idol-select");
    const memberSelect = document.getElementById("member-select");
    
    if(!groupSelect || !memberSelect) return;

    selectedGroup = groupSelect.value;
    memberSelect.innerHTML = '<option value="All">All Members</option>';
    
    if (selectedGroup && KPOP_DATA[selectedGroup]) {
        KPOP_DATA[selectedGroup].members.forEach(member => {
            const opt = document.createElement("option");
            opt.value = member;
            opt.innerText = member;
            memberSelect.appendChild(opt);
        });
        memberSelect.disabled = false;
    } else {
        memberSelect.disabled = true;
    }
}

/**
 * API 호출 및 번역 시작
 */
async function translateAndStart(isRefresh = false) {
    const inputField = document.getElementById("jp-input");
    const textInput = inputField ? inputField.value.trim() : "";
    
    // 1. 메시지 입력 체크
    if (!textInput) {
        alert("Please enter a message!");
        return;
    }

    // 2. [추가] 그룹 선택 여부 체크
    const groupSelect = document.getElementById("idol-select");
    const groupValue = groupSelect ? groupSelect.value : "";

    // 그룹이 선택되지 않았거나 값이 비어있는 경우 (Select Group 상태)
    if (!groupValue || groupValue === "") {
        const currentLang = window.CURRENT_LANG || 'en';
        const msgs = {
            'ko': '먼저 아이돌 그룹을 선택해주세요! ✨',
            'ja': '먼저 아이돌 그룹을 선택해주세요! ✨',
            'en': 'Please select an idol group first! ✨',
            'zh': '请先选择 아이돌 그룹！ ✨'
        };
        alert(msgs[currentLang] || msgs['en']);
        
        // 검색창으로 포커스 이동시켜서 선택 유도
        const searchInput = document.getElementById('group-search-input');
        if(searchInput) searchInput.focus();
        return; // 함수 실행 중단
    }

    selectedGroup = groupValue;

    const memberSelect = document.getElementById("member-select");
    selectedMember = memberSelect ? memberSelect.value : "All";
    
    const langSelect = document.getElementById('src-lang');
    const srcLang = langSelect ? langSelect.value : 'ja';

    // 버튼 상태 변경
    const btn = isRefresh ? document.getElementById("refresh-btn") : document.getElementById("t-btn-gen");
    let originalText = "";
    if(btn) {
        originalText = btn.innerText;
        btn.disabled = true;
        btn.innerText = "Thinking... 💭";
    }

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textInput,
                group: selectedGroup,
                member: selectedMember,
                src_lang: srcLang,
                is_refresh: isRefresh
            })
        });

        const data = await response.json();
        currentOptions = data.result; // 결과 저장
        renderOptions(data.result);
        
        // 화면 전환
        document.getElementById("input-section").style.display = "none";
        document.getElementById("selection-section").style.display = "block";
        document.getElementById("editor-section").style.display = "none";

    } catch (e) {
        console.error(e);
        alert("Error generating slogans. Please try again.");
    } finally {
        if(btn) {
            btn.disabled = false;
            // 버튼 텍스트 복구
            if(isRefresh) {
                if (typeof applyTranslations === 'function') applyTranslations(srcLang);
            } else {
                btn.innerText = originalText;
            }
        }
    }
}

/**
 * 결과 선택지 렌더링
 */
function renderOptions(options) {
    const container = document.getElementById("options-container");
    if (!container) return;
    container.innerHTML = "";

    const labels = ["Name Only", "Cute", "Emotional", "Powerful", "Witty"];

    options.forEach((opt, index) => {
        const card = document.createElement("div");
        card.className = "option-card";
        
        // 애니메이션
        card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;
        card.style.opacity = '0';

        const meaningHtml = opt.meaning ? `<div class="option-meaning">(${opt.meaning})</div>` : '';
        const label = labels[index] || "Style " + (index+1);
        
        card.innerHTML = `
            <div class="option-tag">${label}</div>
            <div class="option-text">${opt.text}</div>
            ${meaningHtml}
        `;
        
        // 클릭 시 에디터로 이동
        card.onclick = () => goToEditor(opt.text, opt.meaning || "");
        container.appendChild(card);
    });
}

/**
 * 에디터 화면으로 이동
 */
function goToEditor(mainText, subText) {
    document.getElementById("selection-section").style.display = "none";
    document.getElementById("editor-section").style.display = "block";
    
    const groupName = selectedGroup || "General";
    const colors = (KPOP_DATA[groupName] && KPOP_DATA[groupName].colors) || ["#ff007f", "#000000"];

    // 1. 팬덤 공식 색상 팔레트 생성
    const colorContainer = document.getElementById("fandom-colors");
    if(colorContainer) {
        colorContainer.innerHTML = "";
        colors.forEach(color => {
            const btn = document.createElement("button");
            btn.className = "color-circle";
            btn.style.backgroundColor = color;
            btn.onclick = () => {
                // [수정] setSolidBg 대신 changeBg 호출
                if(window.changeBg) window.changeBg(color);
                else if(window.setSolidBg) window.setSolidBg(color);
            };
            // 흰색일 경우 테두리 추가
            if(color.toLowerCase() === '#ffffff') btn.style.border = '1px solid #ccc';
            colorContainer.appendChild(btn);
        });
    }

    // 2. 상단 퀵 스위치 버튼 생성
    const switchContainer = document.getElementById('quick-switch-container');
    if(switchContainer) {
        switchContainer.innerHTML = '';
        currentOptions.forEach((item) => {
            const optText = item.text || item;
            const btn = document.createElement('button');
            btn.className = 'control-btn';
            btn.style.fontSize = '12px';
            btn.style.padding = '5px 10px';
            btn.style.flexShrink = '0';
            
            const displayLabel = (optText.length > 7) ? optText.substring(0, 6) + ".." : optText;
            btn.innerText = displayLabel;
            
            btn.onclick = () => {
                // 텍스트 교체 로직 (addTextToCanvas 재호출)
                if (window.addTextToCanvas) {
                    window.addTextToCanvas(optText, item.meaning || "");
                }
            };
            switchContainer.appendChild(btn);
        });
    }

    // 3. 캔버스 초기화 및 텍스트 추가
    if (window.changeOrientation) window.changeOrientation('portrait'); // 기본값 세로
    
    // [수정] 배경색 설정 (에러 수정 포인트)
    if (window.changeBg) window.changeBg(colors[0] || 'white');
    else if (window.setSolidBg) window.setSolidBg(colors[0] || 'white');

    if (window.addTextToCanvas) {
        window.addTextToCanvas(mainText, subText);
    }
    
    // 4. 스티커 로드
    loadStickers();
    
    // 스크롤 상단 이동
    window.scrollTo(0, 0);
}

/**
 * 스티커 로드 함수
 */
function loadStickers() {
    const container = document.getElementById("sticker-container");
    if (!container || container.children.length > 0) return; 

    // [수정] 스크린샷에 있는 실제 파일명(.webp)으로 변경
    const stickers = [
        "star.webp",
        "ribbon1.webp", "ribbon2.webp", "ribbon3.webp", "ribbon4.webp",
        "finger_herat1.webp", "finger_herat2.webp", // 파일명 오타(herat) 그대로 적용
        "cat.webp", "dog.webp", "tiger.webp", "ham.webp",
        "boy.webp", "boy2.webp", "boy_dan.webp",
        "girl_long.webp", "girl_shot.webp", "girl_dan.webp"
    ];

    stickers.forEach(file => {
        const btn = document.createElement("button");
        btn.className = "control-btn img-btn";
        // 이미지 경로가 맞는지 확인 (/static/images/stickers/)
        btn.innerHTML = `<img src="/static/images/stickers/${file}" loading="lazy" alt="sticker">`;
        btn.onclick = () => {
            if(window.addSticker) window.addSticker(file);
        };
        container.appendChild(btn);
    });
}

/**
 * 뒤로 가기 (에디터 -> 선택 화면)
 */
function goBackToSelection() {
    document.getElementById("editor-section").style.display = "none";
    document.getElementById("selection-section").style.display = "block";
    window.scrollTo({ top: 0, behavior: 'smooth' });
}