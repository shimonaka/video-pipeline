/**
 * ビデオパイプライン フロントエンドアプリ
 */

// 要素取得
const scriptInput = document.getElementById('script');
const engineSelect = document.getElementById('engine');
const speakerSelect = document.getElementById('speaker');
const voiceSelect = document.getElementById('voice');
const voicevoxSettings = document.getElementById('voicevoxSettings');
const geminiSettings = document.getElementById('geminiSettings');
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const slideList = document.getElementById('slideList');
const generateBtn = document.getElementById('generateBtn');
const statusDiv = document.getElementById('status');
const resultDiv = document.getElementById('result');
const videoPlayer = document.getElementById('videoPlayer');
const downloadLink = document.getElementById('downloadLink');

// スライド画像の管理
let slides = [];

// エンジン切り替え
engineSelect.addEventListener('change', () => {
    const engine = engineSelect.value;
    if (engine === 'voicevox') {
        voicevoxSettings.classList.remove('hidden');
        geminiSettings.classList.add('hidden');
    } else {
        voicevoxSettings.classList.add('hidden');
        geminiSettings.classList.remove('hidden');
    }
});

// ドロップゾーン
dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

function handleFiles(files) {
    for (const file of files) {
        if (file.type.startsWith('image/')) {
            slides.push(file);
        }
    }
    renderSlideList();
}

function renderSlideList() {
    slideList.innerHTML = '';

    slides.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'slide-item';
        item.draggable = true;
        item.dataset.index = index;

        // プレビュー画像
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        item.appendChild(img);

        // 番号
        const number = document.createElement('span');
        number.className = 'slide-number';
        number.textContent = index + 1;
        item.appendChild(number);

        // 削除ボタン
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-btn';
        removeBtn.textContent = '×';
        removeBtn.onclick = (e) => {
            e.stopPropagation();
            slides.splice(index, 1);
            renderSlideList();
        };
        item.appendChild(removeBtn);

        // ドラッグ&ドロップ
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);

        slideList.appendChild(item);
    });
}

// ドラッグ&ドロップでの並び替え
let dragSrcIndex = null;

function handleDragStart(e) {
    this.classList.add('dragging');
    dragSrcIndex = parseInt(this.dataset.index);
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

function handleDrop(e) {
    e.preventDefault();
    const targetIndex = parseInt(this.dataset.index);

    if (dragSrcIndex !== targetIndex) {
        // 配列を並び替え
        const [movedItem] = slides.splice(dragSrcIndex, 1);
        slides.splice(targetIndex, 0, movedItem);
        renderSlideList();
    }
}

function handleDragEnd() {
    this.classList.remove('dragging');
    dragSrcIndex = null;
}

// 動画生成
generateBtn.addEventListener('click', async () => {
    const script = scriptInput.value.trim();

    if (!script) {
        showStatus('台本を入力してください', true);
        return;
    }

    generateBtn.disabled = true;
    showStatus('⏳ 動画を生成中... (数分かかる場合があります)');
    resultDiv.classList.add('hidden');

    try {
        const formData = new FormData();
        formData.append('script', script);
        formData.append('engine', engineSelect.value);
        formData.append('speaker', speakerSelect.value);
        formData.append('voice', voiceSelect.value);

        // スライドの順番を記録
        const slideOrder = slides.map((_, i) => i).join(',');
        formData.append('slideOrder', slideOrder);

        // スライド画像を追加
        slides.forEach((file, index) => {
            formData.append('slides', file);
        });

        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showStatus('✅ 生成完了！');
            videoPlayer.src = data.videoUrl;
            downloadLink.href = data.videoUrl;
            resultDiv.classList.remove('hidden');
        } else {
            showStatus(`❌ エラー: ${data.error}`, true);
        }

    } catch (error) {
        showStatus(`❌ エラー: ${error.message}`, true);
    } finally {
        generateBtn.disabled = false;
    }
});

function showStatus(message, isError = false) {
    statusDiv.textContent = message;
    statusDiv.className = 'status' + (isError ? ' error' : '');
}
