// Canvas 및 Fabric.js 관련 로직

let canvas;
let currentTextObj = null;

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    initCanvas();
});

function initCanvas() {
    canvas = new fabric.Canvas('c', {
        backgroundColor: '#ffffff',
        preserveObjectStacking: true
    });

    // 텍스트 기본 추가
    addText("Text Here");
}

// 텍스트 추가/수정
function addText(text) {
    if (!canvas) return;
    
    const textObj = new fabric.IText(text, {
        left: canvas.width / 2,
        top: canvas.height / 2,
        fontFamily: 'GmarketSans',
        fill: '#ffffff', // 기본 흰색
        fontSize: 50,
        originX: 'center',
        originY: 'center',
        fontWeight: 'bold',
        stroke: '#ff4081', // 테두리 핑크
        strokeWidth: 2,
        paintFirst: 'stroke',
        textAlign: 'center'
    });

    canvas.add(textObj);
    canvas.setActiveObject(textObj);
    currentTextObj = textObj;
    canvas.renderAll();
}

// 기존 텍스트 교체 (메인 텍스트만)
function replaceMainText(newText) {
    if (!canvas) return;
    
    // 현재 선택된 객체가 텍스트라면 교체, 아니면 기존 i-text 찾아서 교체
    let target = canvas.getActiveObject();
    
    if (!target || target.type !== 'i-text') {
        const objects = canvas.getObjects();
        // 가장 최근에 추가된 i-text를 찾음
        for (let i = objects.length - 1; i >= 0; i--) {
            if (objects[i].type === 'i-text') {
                target = objects[i];
                break;
            }
        }
    }

    if (target && target.type === 'i-text') {
        target.set('text', newText);
        canvas.setActiveObject(target);
        canvas.renderAll();
    } else {
        // 텍스트 객체가 없으면 새로 추가
        addText(newText);
    }
}

// 배경색 변경 (setSolidBg는 main.js 호환용)
function setSolidBg(color) {
    changeBg(color);
}

function changeBg(color) {
    if (!canvas) return;
    canvas.setBackgroundColor(color, canvas.renderAll.bind(canvas));
    // 패턴 이미지가 있다면 제거
    canvas.setBackgroundImage(null, canvas.renderAll.bind(canvas));
}

// 팔레트에서 색상 변경 (텍스트 색상)
function changePalette(input) {
    const color = input.value;
    const activeObj = canvas.getActiveObject();
    if (activeObj && activeObj.type === 'i-text') {
        activeObj.set('fill', color);
        canvas.renderAll();
    } else {
        // 선택된 게 없으면 배경색 변경
        changeBg(color);
    }
}

// 패턴(템플릿) 설정
function setPattern(filename) {
    if (!canvas) return;
    const url = `/static/images/templates/${filename}`;
    fabric.Image.fromURL(url, function(img) {
        img.scaleToWidth(canvas.width);
        img.scaleToHeight(canvas.height);
        canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
            scaleX: canvas.width / img.width,
            scaleY: canvas.height / img.height
        });
        canvas.setBackgroundColor(null, canvas.renderAll.bind(canvas));
    });
}

// 스티커 추가
function addSticker(filename) {
    if (!canvas) return;
    const url = `/static/images/stickers/${filename}`;
    fabric.Image.fromURL(url, function(img) {
        img.scale(0.3); // 적절한 크기로 축소
        img.set({
            left: canvas.width / 2,
            top: canvas.height / 2,
            originX: 'center',
            originY: 'center'
        });
        canvas.add(img);
    });
}

// 방향 전환 (Portrait / Landscape)
function changeOrientation(mode) {
    if (!canvas) return;
    
    if (mode === 'landscape') {
        canvas.setWidth(500);
        canvas.setHeight(350);
    } else {
        canvas.setWidth(350);
        canvas.setHeight(500);
    }
    
    // 중앙 재정렬
    const center = canvas.getCenter();
    canvas.getObjects().forEach(obj => {
        obj.set({
            left: center.left,
            top: center.top
        });
        obj.setCoords();
    });
    
    canvas.renderAll();
}

// [핵심 수정] 이미지 다운로드 (고화질)
function downloadImage() {
    if (!canvas) return;

    // 선택된 객체(테두리 등) 잠시 해제
    canvas.discardActiveObject();
    canvas.renderAll();

    // [개선] 3배 해상도로 저장하여 인쇄 품질 확보
    const dataURL = canvas.toDataURL({
        format: 'png',
        quality: 1.0,
        multiplier: 3  
    });

    const link = document.createElement('a');
    link.download = 'nomujoa_slogan.png';
    link.href = dataURL;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}