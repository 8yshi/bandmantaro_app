document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired. Script loading...');

    const canvas = document.getElementById('setDiagramCanvas');
    if (!canvas) {
        console.error('Canvas element with ID "setDiagramCanvas" not found.');
        return;
    }
    const ctx = canvas.getContext('2d');

    const addRectBtn = document.getElementById('addRectBtn');
    const addCircleBtn = document.getElementById('addCircleBtn');
    const addMicBtn = document.getElementById('addMicBtn');
    const clearBtn = document.getElementById('clearBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const diagramNameInput = document.getElementById('diagramName');
    const propertiesPanel = document.getElementById('propertiesPanel');
    const propText = document.getElementById('propText');
    const propWidth = document.getElementById('propWidth');
    const propHeight = document.getElementById('propHeight');
    const propRadius = document.getElementById('propRadius');
    const propFillColor = document.getElementById('propFillColor');
    const propStrokeColor = document.getElementById('propStrokeColor');
    const propStrokeWidth = document.getElementById('propStrokeWidth');
    const propRotation = document.getElementById('propRotation');
    const deleteBtn = document.getElementById('deleteBtn');
    const rectProps = document.getElementById('rectProps');
    const circleProps = document.getElementById('circleProps');

    let elements = [];
    let selectedElement = null;
    let isDragging = false;
    let dragOffsetX, dragOffsetY;

    const canvasContainer = document.getElementById('canvas-container');
    if (!canvasContainer) {
        console.error('Canvas container element with ID "canvas-container" not found.');
    }

    function resizeCanvas() {
        if (canvasContainer) {
            canvas.width = canvasContainer.clientWidth;
        } else {
            canvas.width = 800; // Fallback
        }
        canvas.height = 400; // Fixed height
        console.log(`Canvas resized to: ${canvas.width}x${canvas.height}`);
        draw(); // Redraw after resize
    }
    window.addEventListener('resize', resizeCanvas);

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // console.log('Drawing elements. Total elements:', elements.length); // デバッグ用ログは頻繁に出すぎないようにコメントアウト

        elements.forEach(el => {
            ctx.save();
            ctx.translate(el.x, el.y);
            ctx.rotate((el.rotation || 0) * Math.PI / 180);

            ctx.fillStyle = el.fillColor || '#ffffff';
            ctx.strokeStyle = el.strokeColor || '#000000';
            ctx.lineWidth = el.strokeWidth || 2;

            if (el.type === 'rect') {
                ctx.fillRect(-el.width / 2, -el.height / 2, el.width, el.height);
                ctx.strokeRect(-el.width / 2, -el.height / 2, el.width, el.height);
            } else if (el.type === 'circle') {
                ctx.beginPath();
                ctx.arc(0, 0, el.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            } else if (el.type === 'mic') {
                const lineLength = 20;
                const radius = 7;
                const arrowHeadSize = 8;
                const totalMicHeight = lineLength + radius * 2;
                const arrowLineTopY = -(totalMicHeight / 2);
                const arrowLineBottomY = arrowLineTopY + lineLength;
                const micHeadCenterY = (totalMicHeight / 2) - radius;

                ctx.beginPath();
                ctx.moveTo(0, arrowLineTopY);
                ctx.lineTo(0, arrowLineBottomY);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(0, arrowLineTopY);
                ctx.lineTo(-arrowHeadSize / 2, arrowLineTopY + arrowHeadSize);
                ctx.lineTo(arrowHeadSize / 2, arrowLineTopY + arrowHeadSize);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();

                ctx.beginPath();
                ctx.arc(0, micHeadCenterY, radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            }

            if (el.text) {
                ctx.fillStyle = el.strokeColor || '#000000';
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';

                let textYOffset = 0;
                if (el.type === 'mic') {
                    const lineLength = 20;
                    const radius = 7;
                    const totalMicHeight = lineLength + radius * 2;
                    textYOffset = -(totalMicHeight / 2) - 15;
                }
                ctx.fillText(el.text, 0, textYOffset);
            }

            ctx.restore();

            if (el === selectedElement) {
                ctx.save();
                ctx.translate(el.x, el.y);
                ctx.rotate((el.rotation || 0) * Math.PI / 180);
                ctx.setLineDash([5, 5]);
                ctx.strokeStyle = 'blue';
                ctx.lineWidth = 3;
                if (el.type === 'rect') {
                    ctx.strokeRect(-el.width / 2, -el.height / 2, el.width, el.height);
                } else if (el.type === 'circle') {
                    ctx.beginPath();
                    ctx.arc(0, 0, el.radius, 0, Math.PI * 2);
                    ctx.stroke();
                } else if (el.type === 'mic') {
                    const lineLength = 20;
                    const radius = 7;
                    const arrowHeadSize = 8;
                    const totalMicHeight = lineLength + radius * 2;
                    const actualWidth = Math.max(arrowHeadSize, radius * 2);

                    const hitBoxPadding = 10; // タッチ操作のためのパディングを増やす
                    const hitBoxLeft = -(actualWidth / 2 + hitBoxPadding);
                    const hitBoxTop = -(totalMicHeight / 2 + hitBoxPadding);
                    const hitBoxWidth = actualWidth + hitBoxPadding * 2;
                    const hitBoxHeight = totalMicHeight + hitBoxPadding * 2;
                    ctx.strokeRect(hitBoxLeft, hitBoxTop, hitBoxWidth, hitBoxHeight);
                }
                ctx.setLineDash([]);
                ctx.restore();
            }
        });
    }

    function addElement(type, x, y) {
        let newElement = {
            type: type,
            x: x,
            y: y,
            text: '',
            fillColor: '#ffffff',
            strokeColor: '#000000',
            strokeWidth: 2,
            rotation: 0
        };
        if (type === 'rect') {
            newElement.width = 80;
            newElement.height = 60;
        } else if (type === 'circle') {
            newElement.radius = 30;
        }
        elements.push(newElement);
        selectedElement = newElement;
        updatePropertiesPanel();
        draw();
    }

    if (addRectBtn) addRectBtn.addEventListener('click', () => addElement('rect', canvas.width / 2, canvas.height / 2));
    if (addCircleBtn) addCircleBtn.addEventListener('click', () => addElement('circle', canvas.width / 2, canvas.height / 2));
    if (addMicBtn) addMicBtn.addEventListener('click', () => addElement('mic', canvas.width / 2, canvas.height / 2));

    if (clearBtn) clearBtn.addEventListener('click', () => {
        elements = [];
        selectedElement = null;
        if (propertiesPanel) propertiesPanel.style.display = 'none';
        draw();
    });

    if (downloadBtn) downloadBtn.addEventListener('click', () => {
        const filename = diagramNameInput ? diagramNameInput.value.trim() || 'セット図' : 'セット図';
        const dataURL = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = dataURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // --- マウスイベント処理 (既存) ---
    canvas.addEventListener('mousedown', handlePointerDown);
    canvas.addEventListener('mousemove', handlePointerMove);
    canvas.addEventListener('mouseup', handlePointerUp);
    canvas.addEventListener('mouseout', handlePointerUp);

    // --- タッチイベント処理 (追加) ---
    // touchstart, touchmove はデフォルトのスクロール/ズームを防ぐためpreventDefault()を呼ぶ
    canvas.addEventListener('touchstart', (e) => {
        e.preventDefault(); // デフォルトのスクロール/ズームを防ぐ
        handlePointerDown(e);
    }, { passive: false }); // passive: false を設定してpreventDefault()を有効にする

    canvas.addEventListener('touchmove', (e) => {
        e.preventDefault(); // デフォルトのスクロール/ズームを防ぐ
        handlePointerMove(e);
    }, { passive: false }); // passive: false を設定してpreventDefault()を有効にする

    canvas.addEventListener('touchend', handlePointerUp);
    canvas.addEventListener('touchcancel', handlePointerUp); // 中断された場合も対応

    // --- イベントハンドラーの共通化 ---
    function getPointerPos(e) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        let clientX, clientY;
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        const mouseX = (clientX - rect.left) * scaleX;
        const mouseY = (clientY - rect.top) * scaleY;
        return { x: mouseX, y: mouseY };
    }

    function handlePointerDown(e) {
        const pos = getPointerPos(e);
        const mouseX = pos.x;
        const mouseY = pos.y;

        selectedElement = null;
        if (propertiesPanel) propertiesPanel.style.display = 'none';

        for (let i = elements.length - 1; i >= 0; i--) {
            const el = elements[i];

            const dx = mouseX - el.x;
            const dy = mouseY - el.y;
            const rad = -((el.rotation || 0) * Math.PI / 180);
            const localX = dx * Math.cos(rad) - dy * Math.sin(rad);
            const localY = dx * Math.sin(rad) + dy * Math.cos(rad);

            const hitBoxPadding = 10; // タッチ操作用の追加パディング

            if (el.type === 'rect') {
                if (localX >= -el.width / 2 - hitBoxPadding && localX <= el.width / 2 + hitBoxPadding &&
                    localY >= -el.height / 2 - hitBoxPadding && localY <= el.height / 2 + hitBoxPadding) {
                    selectedElement = el;
                    break;
                }
            } else if (el.type === 'circle') {
                const dist = Math.sqrt(localX * localX + localY * localY);
                if (dist <= el.radius + hitBoxPadding) {
                    selectedElement = el;
                    break;
                }
            } else if (el.type === 'mic') {
                const lineLength = 20;
                const radius = 7;
                const arrowHeadSize = 8;
                const totalMicHeight = lineLength + radius * 2;
                const actualWidth = Math.max(arrowHeadSize, radius * 2);

                const micHitBoxLeft = -(actualWidth / 2 + hitBoxPadding);
                const micHitBoxTop = -(totalMicHeight / 2 + hitBoxPadding);
                const micHitBoxWidth = actualWidth + hitBoxPadding * 2;
                const micHitBoxHeight = totalMicHeight + hitBoxPadding * 2;

                if (localX >= micHitBoxLeft && localX <= micHitBoxLeft + micHitBoxWidth &&
                    localY >= micHitBoxTop && localY <= micHitBoxTop + micHitBoxHeight) {
                    selectedElement = el;
                    break;
                }
            }
        }

        if (selectedElement) {
            isDragging = true;
            dragOffsetX = mouseX - selectedElement.x;
            dragOffsetY = mouseY - selectedElement.y;
            updatePropertiesPanel();
        }
        draw();
    }

    function handlePointerMove(e) {
        if (isDragging && selectedElement) {
            const pos = getPointerPos(e);
            selectedElement.x = pos.x - dragOffsetX;
            selectedElement.y = pos.y - dragOffsetY;
            draw();
        }
    }

    function handlePointerUp() {
        isDragging = false;
    }

    // プロパティパネルの更新関数
    function updatePropertiesPanel() {
        if (selectedElement) {
            if (propertiesPanel) propertiesPanel.style.display = 'grid';
            if (propText) propText.value = selectedElement.text || '';
            if (propFillColor) propFillColor.value = selectedElement.fillColor || '#ffffff';
            if (propStrokeColor) propStrokeColor.value = selectedElement.strokeColor || '#000000';
            if (propStrokeWidth) propStrokeWidth.value = selectedElement.strokeWidth || 2;
            if (propRotation) propRotation.value = selectedElement.rotation || 0;

            if (rectProps) rectProps.style.display = 'none';
            if (circleProps) circleProps.style.display = 'none';

            if (selectedElement.type === 'rect') {
                if (rectProps) rectProps.style.display = 'block';
                if (propWidth) propWidth.value = selectedElement.width;
                if (propHeight) propHeight.value = selectedElement.height;
            } else if (selectedElement.type === 'circle') {
                if (circleProps) circleProps.style.display = 'block';
                if (propRadius) propRadius.value = selectedElement.radius;
            }
        } else {
            if (propertiesPanel) propertiesPanel.style.display = 'none';
        }
    }

    // プロパティ変更のイベントリスナー (変更なし)
    if (propText) propText.addEventListener('input', (e) => { if (selectedElement) { selectedElement.text = e.target.value; draw(); } });
    if (propWidth) propWidth.addEventListener('input', (e) => { if (selectedElement && selectedElement.type === 'rect') { selectedElement.width = parseInt(e.target.value) || 10; draw(); } });
    if (propHeight) propHeight.addEventListener('input', (e) => { if (selectedElement && selectedElement.type === 'rect') { selectedElement.height = parseInt(e.target.value) || 10; draw(); } });
    if (propRadius) propRadius.addEventListener('input', (e) => { if (selectedElement && selectedElement.type === 'circle') { selectedElement.radius = parseInt(e.target.value) || 5; draw(); } });
    if (propFillColor) propFillColor.addEventListener('input', (e) => { if (selectedElement) { selectedElement.fillColor = e.target.value; draw(); } });
    if (propStrokeColor) propStrokeColor.addEventListener('input', (e) => { if (selectedElement) { selectedElement.strokeColor = e.target.value; draw(); } });
    if (propStrokeWidth) propStrokeWidth.addEventListener('input', (e) => { if (selectedElement) { selectedElement.strokeWidth = parseInt(e.target.value) || 0; draw(); } });
    if (propRotation) propRotation.addEventListener('input', (e) => {
        if (selectedElement) {
            selectedElement.rotation = parseFloat(e.target.value) || 0;
            draw();
        }
    });

    if (deleteBtn) deleteBtn.addEventListener('click', () => {
        if (selectedElement) {
            elements = elements.filter(el => el !== selectedElement);
            selectedElement = null;
            if (propertiesPanel) propertiesPanel.style.display = 'none';
            draw();
        }
    });

    // 初回リサイズとデフォルト要素の定義、そして初回描画の順序
    resizeCanvas();

    elements = [
        { type: 'circle', x: 400, y: 70, radius: 30, text: 'Dr', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 400, y: 150, width: 100, height: 50, text: 'ドラム 2タム', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 150, y: 170, width: 80, height: 60, text: 'Ampeg', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 150, y: 270, radius: 30, text: 'Ba', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 300, y: 170, width: 80, height: 60, text: 'JC', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 300, y: 270, radius: 30, text: 'Gt/Cho', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'mic', x: 280, y: 310, text: '', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 450, y: 270, radius: 30, text: 'Vo', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'mic', x: 450, y: 310, text: '', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 600, y: 170, width: 80, height: 60, text: 'Marshall', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 600, y: 270, radius: 30, text: 'Gt', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 750, y: 170, radius: 30, text: 'Key', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 700, y: 250, width: 100, height: 50, text: 'Key (持込)', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 45 },
    ];

    draw();
    console.log('Initial draw complete.');
});