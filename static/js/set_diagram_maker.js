document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('setDiagramCanvas');
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
    const propRotation = document.getElementById('propRotation'); // 回転入力欄
    const deleteBtn = document.getElementById('deleteBtn');
    const rectProps = document.getElementById('rectProps');
    const circleProps = document.getElementById('circleProps');

    let elements = [];
    let selectedElement = null;
    let isDragging = false;
    let dragOffsetX, dragOffsetY;

    const canvasContainer = document.getElementById('canvas-container');
    function resizeCanvas() {
        canvas.width = canvasContainer.clientWidth;
        canvas.height = 400;
        draw();
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        elements.forEach(el => {
            ctx.save();
            ctx.translate(el.x, el.y);
            ctx.rotate((el.rotation || 0) * Math.PI / 180);

            ctx.fillStyle = '#ffffff';
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;

            if (el.type === 'rect') {
                ctx.fillRect(-el.width / 2, -el.height / 2, el.width, el.height);
                ctx.strokeRect(-el.width / 2, -el.height / 2, el.width, el.height);
            } else if (el.type === 'circle') {
                ctx.beginPath();
                ctx.arc(0, 0, el.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.stroke();
            } else if (el.type === 'mic') {
                const lineLength = 40;
                const radius = 10;
                const arrowHeight = 10;
                const topY = -lineLength / 2;
                const bottomY = lineLength / 2;

                ctx.beginPath();
                ctx.moveTo(0, topY);
                ctx.lineTo(0, bottomY);
                ctx.stroke();

                ctx.beginPath();
                ctx.arc(0, 0, radius, 0, Math.PI * 2);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(0, topY);
                ctx.lineTo(-6, topY + arrowHeight);
                ctx.lineTo(6, topY + arrowHeight);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }

            if (el.text) {
                ctx.fillStyle = el.strokeColor; // テキストは枠線色に合わせる
                ctx.font = '16px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(el.text, 0, el.type === 'mic' ? -30 : 0);
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
                    ctx.strokeRect(-15, -30, 30, 60);
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

    addRectBtn.addEventListener('click', () => addElement('rect', 50, 50));
    addCircleBtn.addEventListener('click', () => addElement('circle', 150, 50));
    addMicBtn.addEventListener('click', () => addElement('mic', 250, 50));

    clearBtn.addEventListener('click', () => {
        elements = [];
        selectedElement = null;
        propertiesPanel.style.display = 'none';
        draw();
    });

    downloadBtn.addEventListener('click', () => {
        const filename = diagramNameInput.value.trim() || 'セット図';
        const dataURL = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `${filename}.png`;
        link.href = dataURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const mouseX = (e.clientX - rect.left) * scaleX;
        const mouseY = (e.clientY - rect.top) * scaleY;

        selectedElement = null;
        propertiesPanel.style.display = 'none';

        // 逆順でヒット判定（上の要素から）
        for (let i = elements.length - 1; i >= 0; i--) {
            const el = elements[i];

            // 回転を考慮した当たり判定：座標を要素のローカル座標系に変換
            const dx = mouseX - el.x;
            const dy = mouseY - el.y;
            const rad = -((el.rotation || 0) * Math.PI / 180); // 逆回転
            const localX = dx * Math.cos(rad) - dy * Math.sin(rad);
            const localY = dx * Math.sin(rad) + dy * Math.cos(rad);

            if (el.type === 'rect') {
                if (localX >= -el.width / 2 && localX <= el.width / 2 &&
                    localY >= -el.height / 2 && localY <= el.height / 2) {
                    selectedElement = el;
                    break;
                }
            } else if (el.type === 'circle') {
                const dist = Math.sqrt(localX * localX + localY * localY);
                if (dist <= el.radius) {
                    selectedElement = el;
                    break;
                }
            } else if (el.type === 'mic') {
                // micの当たり判定は回転後の矩形(幅30、高さ60)の中心0,0基準
                if (localX >= -15 && localX <= 15 &&
                    localY >= -30 && localY <= 30) {
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
    });

    canvas.addEventListener('mousemove', (e) => {
        if (isDragging && selectedElement) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            selectedElement.x = (e.clientX - rect.left) * scaleX - dragOffsetX;
            selectedElement.y = (e.clientY - rect.top) * scaleY - dragOffsetY;
            draw();
        }
    });

    canvas.addEventListener('mouseup', () => {
        isDragging = false;
    });

    canvas.addEventListener('mouseout', () => {
        isDragging = false;
    });

    function updatePropertiesPanel() {
        if (selectedElement) {
            propertiesPanel.style.display = 'grid';
            propText.value = selectedElement.text || '';
            propRotation.value = selectedElement.rotation || 0;

            rectProps.style.display = 'none';
            circleProps.style.display = 'none';

            if (selectedElement.type === 'rect') {
                rectProps.style.display = 'block';
                propWidth.value = selectedElement.width;
                propHeight.value = selectedElement.height;
            } else if (selectedElement.type === 'circle') {
                circleProps.style.display = 'block';
                propRadius.value = selectedElement.radius;
            }
        } else {
            propertiesPanel.style.display = 'none';
        }
    }

    propText.addEventListener('input', (e) => {
        if (selectedElement) {
            selectedElement.text = e.target.value;
            draw();
        }
    });
    propWidth.addEventListener('input', (e) => {
        if (selectedElement && selectedElement.type === 'rect') {
            selectedElement.width = parseInt(e.target.value) || 10;
            draw();
        }
    });
    propHeight.addEventListener('input', (e) => {
        if (selectedElement && selectedElement.type === 'rect') {
            selectedElement.height = parseInt(e.target.value) || 10;
            draw();
        }
    });
    propRadius.addEventListener('input', (e) => {
        if (selectedElement && selectedElement.type === 'circle') {
            selectedElement.radius = parseInt(e.target.value) || 5;
            draw();
        }
    });
    propRotation.addEventListener('input', (e) => {
        if (selectedElement) {
            selectedElement.rotation = parseFloat(e.target.value) || 0;
            draw();
        }
    });

    deleteBtn.addEventListener('click', () => {
        if (selectedElement) {
            elements = elements.filter(el => el !== selectedElement);
            selectedElement = null;
            propertiesPanel.style.display = 'none';
            draw();
        }
    });

    // 1. キャンバスのサイズを確定させる
    resizeCanvas();

    // 2. デフォルトの要素を定義 (elements配列にデータを追加)
    elements = [
        // ドラム (四角形と円)
        { type: 'circle', x: 400, y: 70, radius: 30, text: 'Dr', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 400, y: 150, width: 100, height: 50, text: 'ドラム 2タム', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },

        // Ba (ベース)
        { type: 'rect', x: 150, y: 170, width: 80, height: 60, text: 'Ampeg', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 150, y: 270, radius: 30, text: 'Ba', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },

        // Gt/Cho (ギター/コーラス)
        { type: 'rect', x: 300, y: 170, width: 80, height: 60, text: 'JC', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 300, y: 270, radius: 30, text: 'Gt/Cho', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'mic', x: 280, y: 310, text: '', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 }, // マイクは回転なし

        // Vo (ボーカル)
        { type: 'circle', x: 450, y: 270, radius: 30, text: 'Vo', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'mic', x: 450, y: 310, text: '', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 }, // マイクは回転なし

        // Gt (ギター)
        { type: 'rect', x: 600, y: 170, width: 80, height: 60, text: 'Marshall', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'circle', x: 600, y: 270, radius: 30, text: 'Gt', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },

        // Key (キーボード)
        { type: 'circle', x: 750, y: 170, radius: 30, text: 'Key', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 0 },
        { type: 'rect', x: 700, y: 250, width: 100, height: 50, text: 'Key (持込)', fillColor: '#ffffff', strokeColor: '#000000', strokeWidth: 2, rotation: 45 }, // 45度回転
    ];

    // 3. 定義された要素で初回描画
    draw();
    console.log('Initial draw complete.');
});