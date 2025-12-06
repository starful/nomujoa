// ==========================================
// 1. 그룹별 멤버 & 공식 색상 데이터
// ==========================================
window.GROUP_DATA = {
    "General": { members: [], colors: ["#ff007f", "#000000"] },
    
    "BTS": { 
        members: ["RM", "Jin", "Suga", "J-Hope", "Jimin", "V", "Jungkook"],
        colors: ["#A286B6", "#000000"] 
    },
    "SEVENTEEN": { 
        members: ["S.COUPS", "Jeonghan", "Joshua", "Jun", "Hoshi", "Wonwoo", "Woozi", "The8", "Mingyu", "DK", "Seungkwan", "Vernon", "Dino"],
        colors: ["#F7CAC9", "#92A8D1"] 
    },
    "TWICE": { 
        members: ["Nayeon", "Jeongyeon", "Momo", "Sana", "Jihyo", "Mina", "Dahyun", "Chaeyoung", "Tzuyu"],
        colors: ["#FF5FA2", "#ECCBA6"] 
    },
    "Stray Kids": { 
        members: ["Bang Chan", "Lee Know", "Changbin", "Hyunjin", "Han", "Felix", "Seungmin", "I.N"],
        colors: ["#000000", "#FF0000"] 
    },
    "IVE": { 
        members: ["Yujin", "Gaeul", "Rei", "Wonyoung", "Liz", "Leeseo"],
        colors: ["#FF0055"] 
    },
    "NewJeans": { 
        members: ["Minji", "Hanni", "Danielle", "Haerin", "Hyein"],
        colors: ["#0058C6", "#FFFFFF"] 
    },
    "LE SSERAFIM": { 
        members: ["Sakura", "Chaewon", "Yunjin", "Kazuha", "Eunchae"],
        colors: ["#111111", "#F6F7F9"] 
    },
    "aespa": { 
        members: ["Karina", "Giselle", "Winter", "Ningning"],
        colors: ["#9DE6F5", "#5C5C9F"] 
    },
    "TXT": { 
        members: ["Soobin", "Yeonjun", "Beomgyu", "Taehyun", "HueningKai"],
        colors: ["#79C7E6"] 
    },
    "ENHYPEN": { 
        members: ["Heeseung", "Jay", "Jake", "Sunghoon", "Sunoo", "Jungwon", "Ni-ki"],
        colors: ["#222222"] 
    },
    "ZEROBASEONE": { 
        members: ["Jiwoong", "Hao", "Hanbin", "Matthew", "Taerae", "Ricky", "Gyuvin", "Gunwook", "Yujin"],
        colors: ["#0056B3", "#BCCEE5"] 
    },
    "RIIZE": { 
        members: ["Shotaro", "Eunseok", "Sungchan", "Wonbin", "Sohee", "Anton"],
        colors: ["#F57E2F"] 
    },
    "TREASURE": { 
        members: ["Hyunsuk", "Jihoon", "Yoshi", "Junkyu", "Jaehyuk", "Asahi", "Doyoung", "Haruto", "Jeongwoo", "Junghwan"],
        colors: ["#72C6E7"] 
    },
    "NCT": { 
        members: ["Taeyong", "Mark", "Jaehyun", "Doyoung", "Haechan", "Jaemin", "Jeno", "Jisung", "Chenle", "Renjun", "Johnny", "Yuta", "Jungwoo"],
        colors: ["#B9F306"] 
    }
};

window.kpopData = window.GROUP_DATA;

// ==========================================
// 2. 언어별 추천 문구 (Quick Pick)
// ==========================================
window.quickPhrasesData = {
    "ja": [
        "大好き (좋아해)", "愛してる (사랑해)", "結婚して (결혼해줘)", 
        "会いたい (보고 싶어)", "誕生日おめでとう (생일 축하해)", 
        "応援してる (응원해)", "指ハートして (손하트 해줘)", 
        "尊い (너무 소중해)", "神 (갓벽해)", "顔がいい (얼굴 천재)", 
        "お疲れ様 (수고했어)", "ずっと一緒にいよう (평생 함께하자)",
        "美味しいもの食べてね (맛난 거 먹어)", "風邪ひかないでね (아프지 마)"
    ],
    "en": [
        "I love you", "Love you so much", "Marry me", 
        "Miss you", "Happy Birthday", 
        "Cheer up", "Finger Heart", 
        "So precious", "You are God", "Visual King", 
        "Good job", "Forever with you",
        "Eat delicious food", "Don't get sick"
    ],
    "ko": [
        "사랑해", "진짜 사랑해", "결혼해줘", "보고싶어", "생일 축하해",
        "응원해", "손하트 해줘", "너무 소중해", "신이야", "얼굴 천재",
        "수고했어", "평생 함께하자", "맛난거 먹어", "아프지마"
    ],
    "zh": [
        "我爱你", "非常爱你", "请和我结婚", "想见你", "生日快乐",
        "为你加油", "比心", "尊贵", "神", "脸蛋天才",
        "辛苦了", "一直在一起吧", "吃点好吃的", "别感冒了"
    ]
};

// ==========================================
// 3. UI 텍스트 번역 데이터
// ==========================================
window.uiTranslations = {
    "ja": {
        "desc": "AIが韓国語のファン用語(スラング)に翻訳します✨",
        "label_group": "1. グループ & メンバー (Group)",
        "label_member": "2. 推しメン選択 (Member)",
        "label_quick": "おすすめ (Quick Pick)",
        "label_msg": "3. メッセージ (Message)",
        "btn_gen": "✨ AIに翻訳を頼む",
        "label_bg": "🎨 Background (背景)",
        "label_tpl": "Templates (テンプレート)",
        "label_stk": "✨ Stickers (スタンプ)",
        "btn_save": "💾 画像を保存 (Save Image)",
        "txt_save_desc": "保存した画像はコンビニプリントで印刷できます。<br>(A4サイズ推奨)",
        "label_result": "気に入ったフレーズを選んでね👇",
        "txt_result_desc": "タップして編集へ進む (Tap to edit)",
        "btn_retry": "🔄 他の候補を見る (Try Again)",
        "btn_reset": "最初に戻る (Reset)",
        
        "guide_title": "🎤 Nomujoaの使い方",
        "guide_intro": "Nomujoaは、韓国語がわからなくてもAIが完璧なファンサうちわ文字やスローガンを作ってくれるツールです。",
        "guide_feat_title": "✨ 主な機能",
        "guide_f1": "<strong>AI翻訳:</strong> 「大好き」を入力すると「호랑해(ホランへ)」のようなファン用語に変換！",
        "guide_f2": "<strong>メンバー別対応:</strong> BTS, SEVENTEEN, TWICEなど、メンバーごとの愛称やミームを学習済み。",
        "guide_f3": "<strong>デザイン編集:</strong> 可愛いスタンプや背景を選んで、保存してコンビニで印刷できます。",
        "guide_keys": "関連キーワード: 韓国 アイドル 応援ボード 手作り",

        "seo_title": "Nomujoa - K-POP 推し活ボード & うちわ文字メーカー",
        "seo_desc": "韓国語ができなくても安心！AIが推しへの愛を完璧な韓国語スラングに翻訳。コンサート用ボードやうちわ文字を簡単に作成できます。"
    },
    "en": {
        "desc": "AI translates into Korean Fan Slang! ✨",
        "label_group": "1. Select Group",
        "label_member": "2. Select Member",
        "label_quick": "Quick Pick",
        "label_msg": "3. Message",
        "btn_gen": "✨ Generate Korean Slang",
        "label_bg": "🎨 Background",
        "label_tpl": "Templates",
        "label_stk": "✨ Stickers",
        "btn_save": "💾 Save Image",
        "txt_save_desc": "Perfect for printing on A4 paper or using as a mobile wallpaper.",
        "label_result": "Choose your favorite phrase 👇",
        "txt_result_desc": "Tap to edit",
        "btn_retry": "🔄 Try Again",
        "btn_reset": "Reset",

        "guide_title": "🎤 How to use Nomujoa",
        "guide_intro": "Nomujoa creates professional K-POP concert slogans instantly.",
        "guide_feat_title": "✨ Key Features",
        "guide_f1": "<strong>AI Translation:</strong> Translates 'I love you' into trendy fandom slang.",
        "guide_f2": "<strong>Member Specific:</strong> Supports nicknames for BTS, SVT, TWICE, etc.",
        "guide_f3": "<strong>Design Editor:</strong> Add cute stickers and download.",
        "guide_keys": "Keywords: K-POP Board Maker, Concert Slogan",

        "seo_title": "Nomujoa - K-POP Cheering Board & Uchiwa Maker",
        "seo_desc": "Create professional K-POP concert slogans and Uchiwa fans instantly with AI translation. Translate 'I love you' to trendy Korean fandom slang."
    },
    "ko": {
        "desc": "AI가 한국어 팬덤 용어(주접 멘트)로 번역해줍니다 ✨",
        "label_group": "1. 그룹 선택",
        "label_member": "2. 멤버 선택",
        "label_quick": "빠른 선택 (추천)",
        "label_msg": "3. 메시지 입력",
        "btn_gen": "✨ 번역하기",
        "label_bg": "🎨 배경 설정",
        "label_tpl": "템플릿",
        "label_stk": "✨ 스티커",
        "btn_save": "💾 이미지 저장",
        "txt_save_desc": "A4 사이즈로 인쇄하거나 폰 배경으로 쓰세요.",
        "label_result": "마음에 드는 문구를 고르세요 👇",
        "txt_result_desc": "클릭하면 편집할 수 있습니다.",
        "btn_retry": "🔄 다른 문구 보기",
        "btn_reset": "처음으로",

        "guide_title": "🎤 Nomujoa 사용법",
        "guide_intro": "한국어를 몰라도 OK! AI가 주접 멘트로 슬로건을 만들어줍니다.",
        "guide_feat_title": "✨ 주요 기능",
        "guide_f1": "<strong>AI 번역:</strong> 단순 번역이 아닌 팬덤 용어로 변환.",
        "guide_f2": "<strong>멤버별 맞춤:</strong> 그룹별, 멤버별 별명 완벽 이해.",
        "guide_f3": "<strong>디자인 에디터:</strong> 꾸미고 저장하여 바로 인쇄하세요.",
        "guide_keys": "키워드: 케이팝 응원 보드, 우치와 제작",

        "seo_title": "Nomujoa (노무조아) - K-POP 주접 멘트 번역기 & 응원 보드",
        "seo_desc": "한국어를 몰라도 OK! AI가 아이돌 팬덤 용어로 번역해주는 무료 서비스. 콘서트 슬로건, 전광판, 우치와를 3초 만에 만들어보세요."
    },
    "zh": {
        "desc": "AI将为您翻译成韩语粉丝用语✨",
        "label_group": "1. 选择组合",
        "label_member": "2. 选择成员",
        "label_quick": "推荐语句",
        "label_msg": "3. 输入信息",
        "btn_gen": "✨ AI 翻译",
        "label_bg": "🎨 背景设置",
        "label_tpl": "模板",
        "label_stk": "✨ 贴纸",
        "btn_save": "💾 保存图片",
        "txt_save_desc": "建议打印为A4尺寸。",
        "label_result": "请选择喜欢的语句 👇",
        "txt_result_desc": "点击进行编辑",
        "btn_retry": "🔄 再试一次",
        "btn_reset": "重置",

        "guide_title": "🎤 如何使用 Nomujoa",
        "guide_intro": "即使不懂韩语，AI也能为您制作完美的应援板。",
        "guide_feat_title": "✨ 主要功能",
        "guide_f1": "<strong>AI 翻译:</strong> 翻译成流行的饭圈用语。",
        "guide_f2": "<strong>成员专属:</strong> 支持 BTS, SEVENTEEN 等成员昵称。",
        "guide_f3": "<strong>设计编辑:</strong> 添加贴纸，下载打印。",
        "guide_keys": "关键词: 韩语应援板, 演唱会手幅",

        "seo_title": "Nomujoa - K-POP 应援板 & 扇子制作工具",
        "seo_desc": "即使不懂韩语也能制作完美的应援板！AI自动翻译成流行的韩语饭圈用语。"
    }
};