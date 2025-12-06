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

    const map = {
        "t-desc": t.desc,
        "t-label-group": t.label_group,
        "t-label-member": t.label_member,
        "t-label-quick": t.label_quick,
        "t-label-msg": t.label_msg,
        "t-btn-gen": t.btn_gen,
        "t-label-result": t.label_result,
        "t-txt-result-desc": t.txt_result_desc,
        "t-btn-retry": t.btn_retry, 
        "t-label-bg": t.label_bg,
        "t-label-tpl": t.label_tpl,
        "t-label-stk": t.label_stk,
        "t-btn-save": t.btn_save,
        "t-txt-save-desc": t.txt_save_desc,
        "t-guide-title": t.guide_title,
        "t-guide-intro": t.guide_intro,
        "t-guide-feat-title": t.guide_feat_title,
        "t-guide-f1": t.guide_f1,
        "t-guide-f2": t.guide_f2,
        "t-guide-f3": t.guide_f3,
        "t-guide-keys": t.guide_keys
    };

    for (const [id, text] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = text;
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

    if (kpopData[selectedGroup] && kpopData[selectedGroup].members) {
        memberSelect.disabled = false;
        kpopData[selectedGroup].members.forEach(member => {
            const option = document.createElement("option");
            option.value = member;
            option.text = member;
            memberSelect.appendChild(option);
        });
    }
}

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
        currentOptions = data.result;

        document.getElementById('input-section').style.display = 'none';
        const selectSection = document.getElementById('selection-section');
        const container = document.getElementById('options-container');
        
        selectSection.style.display = 'block';
        container.innerHTML = ''; 

        const labels = ["Name Only", "Cute", "Emotional", "Powerful", "Wit"];
        
        currentOptions.forEach((optText, index) => {
            const card = document.createElement('div');
            card.className = 'option-card';
            card.onclick = function() { goToEditor(optText); };
            
            card.style.animation = `fadeIn 0.5s ease forwards ${index * 0.1}s`;
            card.style.opacity = '0';

            const label = labels[index] || "Style " + (index+1);
            card.innerHTML = `<span class="option-tag">${label}</span><div class="option-text">${optText}</div>`;
            container.appendChild(card);
        });

    } catch (e) {
        alert("Error: " + e);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
        applyTranslations(srcLang); 
        
        if(refreshBtn) {
            refreshBtn.disabled = false;
        }
    }
}

function goToEditor(selectedText) {
    document.getElementById('selection-section').style.display = 'none';
    document.getElementById('editor-section').style.display = 'block';

    const groupSelect = document.getElementById("idol-select");
    const groupName = groupSelect.value || "General";
    const colors = kpopData[groupName]?.colors || ["#ff007f", "#000000"];
    
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
        currentOptions.forEach((opt, idx) => {
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
    setSolidBg(colors[0]); // canvas.js의 changeBg 호출
    addText(selectedText); 
}