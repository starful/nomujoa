// static/js/main.js

// 전역 변수로 현재 AI 번역 결과 옵션을 저장합니다.
let currentOptions = [];

// [개선] 페이지의 모든 리소스(폰트 포함)가 로드된 후 캔버스를 다시 렌더링하여 글꼴 깨짐을 방지합니다.
window.addEventListener('load', function() {
    document.fonts.ready.then(function () {
        console.log('Fonts are fully loaded.');
        // canvas 객체가 초기화된 후에만 렌더링을 요청합니다.
        if(typeof canvas !== 'undefined' && canvas) {
            canvas.requestRenderAll();
        }
    });
});

// [핵심 수정] DOM이 준비되면 UI를 초기화하는 로직
document.addEventListener('DOMContentLoaded', function() {
    // 페이지 로드 시점에 단 한 번, updateUI()를 호출합니다.
    // 이 함수가 현재 언어 설정에 맞게 모든 텍스트와 추천 문구를 설정합니다.
    updateUI();

    // 키보드의 Delete 또는 Backspace 키로 캔버스 위의 선택된 객체를 삭제하는 이벤트 리스너입니다.
    document.addEventListener('keydown', function(e) {
        // 입력 필드에 포커스가 있을 때는 작동하지 않도록 합니다.
        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            if (e.key === 'Delete' || e.key === 'Backspace') {
                const activeObj = canvas.getActiveObject();
                // 텍스트 편집 중이 아닐 때만 객체를 삭제합니다.
                if (activeObj && !activeObj.isEditing) { 
                    canvas.remove(activeObj);
                    canvas.requestRenderAll();
                }
            }
        }
    });
});

/**
 * [통합된 UI 업데이트 함수]
 * 페이지의 언어 설정에 맞춰 모든 UI 텍스트와 동적 컨텐츠(추천 문구)를 업데이트합니다.
 */
function updateUI() {
    const langSelect = document.getElementById('src-lang');
    // <select> 요소가 없으면 함수를 종료합니다. (가이드 페이지 등 예외 처리)
    if (!langSelect) return; 
    
    const selectedLang = langSelect.value;

    // 1. 입력창의 플레이스홀더(예시 문구)를 변경합니다.
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

    // 2. 추천 문구(Quick Pick) 버튼들을 현재 언어에 맞게 다시 렌더링합니다.
    renderQuickPhrases(selectedLang);

    // 3. 페이지의 나머지 모든 UI 텍스트를 번역합니다.
    applyTranslations(selectedLang);
}

/**
 * UI 요소들의 텍스트를 선택된 언어에 맞게 변경합니다.
 * @param {string} lang - 'ja', 'en', 'ko', 'zh' 등 언어 코드
 */
function applyTranslations(lang) {
    const t = uiTranslations[lang] || uiTranslations['en']; // 해당 언어 번역이 없으면 영어로 대체

    // 헬퍼 함수: ID를 찾아 텍스트를 교체합니다.
    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = text;
    }

    // 각 UI 요소에 번역된 텍스트를 적용합니다.
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
    
    // '처음으로' 버튼과 같이 여러 곳에서 사용되는 클래스 기반 번역
    const resetBtns = document.querySelectorAll('.reset-link');
    resetBtns.forEach(btn => btn.innerText = t.btn_reset);

    // SEO 관련 메타 태그들도 동적으로 변경합니다.
    if (t.seo_title) document.title = t.seo_title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && t.seo_desc) metaDesc.setAttribute("content", t.seo_desc);
    
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogTitle && t.seo_title) ogTitle.setAttribute("content", t.seo_title);
    if (ogDesc && t.seo_desc) ogDesc.setAttribute("content", t.seo_desc);
}

/**
 * 추천 문구(Quick Pick) 영역을 현재 언어에 맞게 다시 그립니다.
 * @param {string} lang - 언어 코드
 */
function renderQuickPhrases(lang) {
    const container = document.getElementById('quick-phrase-container');
    if (!container) return;
    container.innerHTML = ''; // 기존 버튼들을 모두 지웁니다.

    // data.js에서 현재 언어에 맞는 추천 문구 목록을 가져옵니다. 없으면 영어를 기본값으로 사용합니다.
    const phrases = quickPhrasesData[lang] || quickPhrasesData['en'];

    phrases.forEach(phrase => {
        // 일본어의 경우 "大好き (좋아해)" 형태이므로, 괄호 안의 한국어는 실제 입력값에서 제외합니다.
        const displayPhrase = phrase; 
        const inputPhrase = phrase.split(' (')[0]; 

        const chip = document.createElement('div');
        chip.className = 'phrase-chip';
        chip.innerText = displayPhrase;
        
        // 버튼 클릭 시, 입력창에 값을 넣고 언어 설정을 맞춘 뒤 바로 번역을 시작합니다.
        chip.onclick = function() {
            const inputField = document.getElementById('jp-input');
            inputField.value = inputPhrase;
            
            const langSelect = document.getElementById('src-lang');
            if(langSelect) langSelect.value = lang;
            
            translateAndStart();
        };
        container.appendChild(chip);
    });
}

/**
 * K-POP 그룹 선택 시, 해당 그룹의 멤버 목록을 드롭다운에 채웁니다.
 */
function updateMembers() {
    const groupSelect = document.getElementById("idol-select");
    const memberSelect = document.getElementById("member-select");
    const selectedGroup = groupSelect.value;

    memberSelect.innerHTML = '<option value="All">All Members</option>'; // 기본값으로 '전체 멤버' 추가
    memberSelect.disabled = true;

    // index.html에서 Flask를 통해 주입된 그룹 데이터를 사용합니다.
    const data = window.GROUP_DATA || window.kpopData;

    if (selectedGroup && data[selectedGroup] && data[selectedGroup].members) {
        memberSelect.disabled = false;
        data[selectedGroup].members.forEach(member => {
            const option = document.createElement("option");
            option.value = member;
            option.text = member;
            memberSelect.appendChild(option);
        });
    }
}

/**
 * AI 번역을 요청하고, 결과를 받아 화면을 전환하는 메인 함수입니다.
 * @param {boolean} isRefresh - 새로운 추천을 받기 위한 재요청 여부
 */
async function translateAndStart(isRefresh = false) {
    // 입력 요소들로부터 현재 값들을 가져옵니다.
    const inputField = document.getElementById('jp-input');
    const groupSelect = document.getElementById('idol-select');
    const memberSelect = document.getElementById('member-select');
    const langSelect = document.getElementById('src-lang');
    
    const text = inputField.value;
    const group = groupSelect.value;
    const member = memberSelect.value;
    const srcLang = langSelect.value;

    // 유효성 검사
    if (!text) return alert("Please enter a message!");
    if (!group) return alert("Please select a group!");

    // 로딩 상태 시작: 버튼 비활성화 및 텍스트 변경
    const btn = document.querySelector('.primary-btn');
    const originalText = btn.innerHTML; // innerHTML로 변경하여 아이콘 등 유지
    btn.innerHTML = "Thinking... 💭";
    btn.disabled = true;

    const refreshBtn = document.getElementById('refresh-btn');
    if(refreshBtn) {
        refreshBtn.disabled = true;
        // 새로고침 버튼 텍스트도 번역 적용
        const refreshOriginalText = refreshBtn.innerHTML; 
    }

    try {
        // 서버 API에 번역 요청
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: text, 
                group: group, 
                member: member, 
                src_lang: srcLang, 
                is_refresh: isRefresh 
            })
        });
        
        const data = await response.json();
        currentOptions = data.result; // 결과 저장: [{text: "...", meaning: "..."}, ...]

        // 화면 전환 및 결과 표시
        document.getElementById('input-section').style.display = 'none';
        const selectSection = document.getElementById('selection-section');
        const container = document.getElementById('options-container');
        
        selectSection.style.display = 'block';
        container.innerHTML = ''; // 이전 결과 삭제

        // 서버에서 받은 5개의 추천 문구를 카드로 만듭니다.
        const labels = ["Name Only", "Cute", "Emotional", "Powerful", "Witty"];
        currentOptions.forEach((item, index) => {
            const koreanText = item.text || "Error"; 
            const meaningText = item.meaning || text; 

            const card = document.createElement('div');
            card.className = 'option-card';
            
            // 카드를 클릭하면 해당 한국어 텍스트를 가지고 에디터 화면으로 이동합니다.
            card.onclick = function() { goToEditor(koreanText); };
            
            // 카드들이 순차적으로 나타나는 애니메이션 효과
            card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;
            card.style.opacity = '0';

            const label = labels[index] || "Style " + (index+1);
            
            card.innerHTML = `
                <span class="option-tag">${label}</span>
                <div class="option-text">${koreanText}</div>
                <div class="option-meaning">(${meaningText})</div>
            `;
            container.appendChild(card);
        });

    } catch (e) {
        alert("An error occurred during translation: " + e.message);
        console.error(e);
    } finally {
        // 로딩 상태 종료: 버튼 원래대로 복구
        btn.innerHTML = originalText;
        btn.disabled = false;
        if(refreshBtn) {
            refreshBtn.disabled = false;
            // 버튼 텍스트도 번역된 상태로 복구
            applyTranslations(srcLang); 
        }
    }
}

/**
 * 사용자가 선택한 문구로 에디터 화면을 설정하고 보여줍니다.
 * @param {string} selectedText - 사용자가 선택한 한국어 문구
 */
function goToEditor(selectedText) {
    document.getElementById('selection-section').style.display = 'none';
    document.getElementById('editor-section').style.display = 'block';

    const groupSelect = document.getElementById("idol-select");
    const groupName = groupSelect.value || "General";
    
    const data = window.GROUP_DATA || window.kpopData;
    const colors = data[groupName]?.colors || ["#ff007f", "#000000"];
    
    // 팬덤 공식 색상 버튼을 만듭니다.
    const colorContainer = document.getElementById('fandom-colors');
    if(colorContainer) {
        colorContainer.innerHTML = ''; 
        colors.forEach(color => {
            const btn = document.createElement('button');
            btn.className = 'control-btn color-circle';
            btn.style.backgroundColor = color;
            btn.setAttribute('aria-label', `Set background to ${color}`);
            btn.onclick = () => setSolidBg(color);
            if(color.toLowerCase() === '#ffffff') btn.style.border = '1px solid #ccc';
            colorContainer.appendChild(btn);
        });
    }

    // 에디터 상단에 다른 추천 문구로 빠르게 교체할 수 있는 버튼들을 만듭니다.
    const switchContainer = document.getElementById('quick-switch-container');
    if(switchContainer) {
        switchContainer.innerHTML = '';
        currentOptions.forEach((item, idx) => {
            const opt = item.text || item;
            
            const btn = document.createElement('button');
            btn.className = 'control-btn';
            btn.style.fontSize = '12px';
            btn.style.padding = '5px 10px';
            btn.style.flexShrink = '0'; // 버튼이 줄어들지 않도록 설정
            
            const displayLabel = (opt.length > 7) ? opt.substring(0, 6) + ".." : opt;
            btn.innerText = displayLabel;
            btn.onclick = () => replaceMainText(opt);
            switchContainer.appendChild(btn);
        });
    }

    // 캔버스 초기 설정
    changeOrientation('portrait'); 
    canvas.clear();
    setSolidBg(colors[0] || '#ffffff'); 
    addText(selectedText); 
}

/**
 * 에디터 화면에서 '목록으로 돌아가기' 버튼 클릭 시 실행됩니다.
 */
function goBackToSelection() {
    document.getElementById('editor-section').style.display = 'none';
    document.getElementById('selection-section').style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}