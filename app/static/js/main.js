// static/js/main.js

let currentOptions = [];

// [개선] 폰트 로딩 대기 후 캔버스 렌더링 (글꼴 깨짐 방지)
window.addEventListener('load', function() {
    document.fonts.ready.then(function () {
        console.log('Fonts loaded.');
        if(typeof canvas !== 'undefined') {
            canvas.requestRenderAll();
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    renderQuickPhrases('ja'); // 기본 일본어
});

document.addEventListener('keydown', function(e) {
    if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            const activeObj = canvas.getActiveObject();
            if (activeObj && !activeObj.isEditing) { 
                canvas.remove(activeObj);
                canvas.requestRenderAll();
            }
        }
    }
});

// [통합] 언어 변경 시 UI 업데이트
function updateUI() {
    const langSelect = document.getElementById('src-lang');
    const selectedLang = langSelect.value;

    // 1. 입력창 예시 변경
    const inputField = document.getElementById('jp-input');
    const placeholders = {
        "ja": "例: 大好き、結婚して",
        "en": "e.g., I love you, Marry me",
        "ko": "예: 사랑해, 완전 멋져",
        "zh": "例如：我爱你, 请和我结婚"
    };
    if (placeholders[selectedLang]) {
        inputField.placeholder = placeholders[selectedLang];
    }

    // 2. 추천 문구 변경
    renderQuickPhrases(selectedLang);

    // 3. UI 텍스트 번역 적용
    applyTranslations(selectedLang);
}

// 텍스트 번역 적용
function applyTranslations(lang) {
    const t = uiTranslations[lang] || uiTranslations['en'];

    // 헬퍼 함수: ID가 있으면 텍스트 교체
    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = text;
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
    
    // [추가] 돌아가기 버튼 번역 적용
    setText("t-btn-back-list", t.btn_back_list);
    
    setText("t-txt-save-desc", t.txt_save_desc);
    
    // 가이드 섹션 (메인 페이지에서 제거되었어도 에러 방지용으로 남겨둠)
    if(t.guide_title) {
        setText("t-guide-title", t.guide_title);
        setText("t-guide-intro", t.guide_intro);
        setText("t-guide-feat-title", t.guide_feat_title);
        setText("t-guide-f1", t.guide_f1);
        setText("t-guide-f2", t.guide_f2);
        setText("t-guide-f3", t.guide_f3);
        setText("t-guide-keys", t.guide_keys);
    }

    const resetBtns = document.querySelectorAll('.reset-link');
    resetBtns.forEach(btn => btn.innerText = t.btn_reset);

    // 메타 태그 업데이트
    if (t.seo_title) document.title = t.seo_title;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && t.seo_desc) metaDesc.setAttribute("content", t.seo_desc);
    
    const ogTitle = document.querySelector('meta[property="og:title"]');
    const ogDesc = document.querySelector('meta[property="og:description"]');
    
    if (ogTitle && t.seo_title) ogTitle.setAttribute("content", t.seo_title);
    if (ogDesc && t.seo_desc) ogDesc.setAttribute("content", t.seo_desc);
}

function renderQuickPhrases(lang) {
    const container = document.getElementById('quick-phrase-container');
    if (!container) return;
    container.innerHTML = '';

    const phrases = quickPhrasesData[lang] || quickPhrasesData['en'];

    phrases.forEach(phrase => {
        const displayPhrase = phrase; 
        const inputPhrase = phrase.split(' (')[0]; 

        const chip = document.createElement('div');
        chip.className = 'phrase-chip';
        chip.innerText = displayPhrase;
        
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

function updateMembers() {
    const groupSelect = document.getElementById("idol-select");
    const memberSelect = document.getElementById("member-select");
    const selectedGroup = groupSelect.value;

    memberSelect.innerHTML = '<option value="All">All Members</option>';
    memberSelect.disabled = true;

    // window.GROUP_DATA (또는 kpopData) 사용
    const data = window.GROUP_DATA || window.kpopData;

    if (data[selectedGroup] && data[selectedGroup].members) {
        memberSelect.disabled = false;
        data[selectedGroup].members.forEach(member => {
            const option = document.createElement("option");
            option.value = member;
            option.text = member;
            memberSelect.appendChild(option);
        });
    }
}

// [수정] 번역 및 UI 표시 로직 (의미 표시 추가)
async function translateAndStart(isRefresh = false) {
    const inputField = document.getElementById('jp-input');
    const groupSelect = document.getElementById('idol-select');
    const memberSelect = document.getElementById('member-select');
    const langSelect = document.getElementById('src-lang');
    
    const text = inputField.value;
    const group = groupSelect.value;
    const member = memberSelect.value;
    const srcLang = langSelect.value;

    if (!text) return alert("Please enter a message!");
    if (!group) return alert("Please select a group!");

    const btn = document.querySelector('.primary-btn');
    const originalText = btn.innerText;
    btn.innerText = "Thinking... 💭";
    btn.disabled = true;

    const refreshBtn = document.getElementById('refresh-btn');
    if(refreshBtn) {
        refreshBtn.innerText = "Loading...";
        refreshBtn.disabled = true;
    }

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: text, group: group, member: member, 
                src_lang: srcLang, is_refresh: isRefresh 
            })
        });
        
        const data = await response.json();
        currentOptions = data.result; // [{text: "...", meaning: "..."}, ...]

        document.getElementById('input-section').style.display = 'none';
        const selectSection = document.getElementById('selection-section');
        const container = document.getElementById('options-container');
        
        selectSection.style.display = 'block';
        container.innerHTML = ''; 

        const labels = ["Name Only", "Cute", "Emotional", "Powerful", "Wit"];
        
        currentOptions.forEach((item, index) => {
            const koreanText = item.text || item; 
            const meaningText = item.meaning || text; 

            const card = document.createElement('div');
            card.className = 'option-card';
            
            // 편집기로 넘어갈 때는 한국어 텍스트만 전달
            card.onclick = function() { goToEditor(koreanText); };
            
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
        alert("Error: " + e);
        console.error(e);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
        applyTranslations(srcLang); 
        
        if(refreshBtn) {
            refreshBtn.disabled = false;
        }
    }
}

// [수정] 에디터 이동 로직
function goToEditor(selectedText) {
    document.getElementById('selection-section').style.display = 'none';
    document.getElementById('editor-section').style.display = 'block';

    const groupSelect = document.getElementById("idol-select");
    const groupName = groupSelect.value || "General";
    
    // 데이터 소스 확인
    const data = window.GROUP_DATA || window.kpopData;
    const colors = data[groupName]?.colors || ["#ff007f", "#000000"];
    
    const colorContainer = document.getElementById('fandom-colors');
    if(colorContainer) {
        colorContainer.innerHTML = ''; 
        colors.forEach(color => {
            const btn = document.createElement('button');
            btn.className = 'control-btn color-circle';
            btn.style.backgroundColor = color;
            btn.onclick = () => changeBg(color);
            if(color.toLowerCase() === '#ffffff') btn.style.border = '1px solid #ccc';
            colorContainer.appendChild(btn);
        });
    }

    const switchContainer = document.getElementById('quick-switch-container');
    if(switchContainer) {
        switchContainer.innerHTML = '';
        currentOptions.forEach((item, idx) => {
            const opt = item.text || item;
            
            const btn = document.createElement('button');
            btn.className = 'control-btn';
            btn.style.fontSize = '12px';
            btn.style.padding = '5px 10px';
            btn.style.flexShrink = '0'; 
            
            const displayLabel = (idx === 0) ? "Name" : (opt.length > 6 ? opt.substring(0,6)+".." : opt);
            btn.innerText = displayLabel;
            btn.onclick = () => replaceMainText(opt);
            switchContainer.appendChild(btn);
        });
    }

    changeOrientation('portrait'); 
    canvas.clear();
    setSolidBg(colors[0]); 
    addText(selectedText); 
}

// [추가] 목록으로 돌아가기 기능
function goBackToSelection() {
    // 1. 에디터 화면 숨기기
    document.getElementById('editor-section').style.display = 'none';
    
    // 2. 선택(목록) 화면 보여주기
    document.getElementById('selection-section').style.display = 'block';
    
    // 3. 스크롤을 부드럽게 위로 올림
    window.scrollTo({ top: 0, behavior: 'smooth' });
}