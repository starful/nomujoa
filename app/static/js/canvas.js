// app/static/js/canvas.js

let canvas;
let activeTextObject = null; // 현재 활성화된 텍스트 객체를 추적

// 캔버스 초기화
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('c')) {
        canvas = new fabric.Canvas('c', {
            backgroundColor: '#FFFFFF',
            preserveObjectStacking: true
        });

        // 캔버스에서 선택이 해제되었을 때 activeTextObject를 null로 설정
        canvas.on('selection:cleared', function() {
            activeTextObject = null;
        });

        // 객체가 선택되었을 때 activeTextObject를 업데이트
        canvas.on('selection:created', function(e) {
            if (e.target && e.target.type === 'i-text') {
                activeTextObject = e.target;
            }
        });
        
        canvas.on('selection:updated', function(e) {
            if (e.target && e.target.type === 'i-text') {
                activeTextObject = e.target;
            }
        });
    }
});


// 텍스트 객체를 캔버스에 추가하는 함수
function addTextToCanvas(text, options = {}) {
    if (!canvas) return;

    // 기존 텍스트 객체 제거
    if (activeTextObject) {
        canvas.remove(activeTextObject);
    }

    const textObj = new fabric.IText(text, {
        left: canvas.width / 2,
        top: canvas.height / 2,
        originX: 'center',
        originY: 'center',
        fontFamily: options.font || 'GmarketSans',
        fill: options.color || '#333333',
        stroke: options.stroke || '#FFFFFF',
        strokeWidth: options.strokeWidth || 1.2,
        paintFirst: 'stroke',
        fontSize: 60,
        textAlign: 'center',
        // [수정] 'alphabetical' -> 'alphabetic'
        textBaseline: 'alphabetic', 
        lineHeight: 1.2,
        styles: options.styles || {}
    });

    canvas.add(textObj);
    canvas.setActiveObject(textObj);
    activeTextObject = textObj; // 새로운 텍스트 객체를 활성 객체로 설정
    canvas.renderAll();
}

// 방향 전환 함수
function changeOrientation(orientation) {
    if (!canvas) return;
    if (orientation === 'portrait') {
        canvas.setWidth(350);
        canvas.setHeight(500);
    } else {
        canvas.setWidth(500);
        canvas.setHeight(350);
    }
    canvas.getObjects().forEach(obj => {
        obj.center();
    });
    canvas.renderAll();
}

// 배경색 변경 함수
function changeBg(color) {
    if (!canvas) return;
    canvas.setBackgroundColor(color, canvas.renderAll.bind(canvas));
    canvas.backgroundImage = null; // 배경 이미지 제거
}

// 배경 패턴 설정 함수
function setPattern(patternName) {
    if (!canvas) return;
    const imgURL = `/static/images/templates/${patternName}`;
    fabric.Image.fromURL(imgURL, function(img) {
        canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
            scaleX: canvas.width / img.width,
            scaleY: canvas.height / img.height
        });
    });
}

// 스티커 추가 함수
function addSticker(stickerName) {
    if (!canvas) return;
    const stickerUrl = `/static/images/stickers/${stickerName}`;
    fabric.Image.fromURL(stickerUrl, function(img) {
        img.scale(0.3);
        img.set({
            left: canvas.width / 2,
            top: canvas.height / 3,
            originX: 'center',
            originY: 'center',
        });
        canvas.add(img);
        canvas.setActiveObject(img);
    }, { crossOrigin: 'anonymous' });
}


// 팔레트 색상 변경
function changePalette(colorPicker) {
    if (!canvas) return;
    const color = colorPicker.value;
    const activeObject = canvas.getActiveObject();

    if (activeObject && activeObject.type === 'i-text') {
        activeObject.set('fill', color);
        canvas.renderAll();
    }
}


// 이미지 다운로드 함수
function downloadImage() {
    if (!canvas) return;
    const dataURL = canvas.toDataURL({
        format: 'png',
        quality: 1.0
    });
    const link = document.createElement('a');
    link.href = dataURL;
    link.download = 'nomujoa_design.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}