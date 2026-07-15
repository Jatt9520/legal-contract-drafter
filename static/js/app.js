/**
 * 法律合同拟写助手 — 前端交互逻辑
 */

// ============ 通知系统 ============
function showNotification(message, type = 'info') {
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const el = document.createElement('div');
    el.className = `notification ${type}`;
    el.textContent = message;
    document.body.appendChild(el);

    setTimeout(() => el.remove(), 3000);
}

// ============ 加载遮罩 ============
function showLoading(text = '正在处理...') {
    let overlay = document.getElementById('loadingOverlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <p id="loadingText">${text}</p>
            </div>
        `;
        document.body.appendChild(overlay);
    } else {
        overlay.style.display = 'flex';
        const loadingText = document.getElementById('loadingText');
        if (loadingText) loadingText.textContent = text;
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}

// ============ AI 合同生成 ============
function generateAIContract() {
    const contractType = document.getElementById('aiContractType')?.value || '';
    const partyA = document.getElementById('aiPartyA')?.value || '';
    const partyB = document.getElementById('aiPartyB')?.value || '';
    const description = document.getElementById('aiDescription')?.value || '';
    const keyTermsStr = document.getElementById('aiKeyTerms')?.value || '';

    if (!description.trim()) {
        showNotification('请输入合同需求描述', 'error');
        return;
    }

    const keyTerms = keyTermsStr.split(/[,，]/).map(t => t.trim()).filter(Boolean);

    // 创建流式输出区域
    const aiContainer = document.querySelector('.ai-container');
    let streamOutput = document.getElementById('aiStreamOutput');
    if (!streamOutput) {
        streamOutput = document.createElement('div');
        streamOutput.id = 'aiStreamOutput';
        streamOutput.className = 'ai-stream-output';
        streamOutput.innerHTML = '<p>正在生成合同内容...<span class="cursor"></span></p>';
        aiContainer.appendChild(streamOutput);
    } else {
        streamOutput.style.display = 'block';
        streamOutput.innerHTML = '<p>正在生成合同内容...<span class="cursor"></span></p>';
    }

    // 发起 SSE 请求
    const url = '/api/contract/ai-generate';
    const body = JSON.stringify({
        contract_type: contractType || null,
        description: description,
        party_a_name: partyA || null,
        party_b_name: partyB || null,
        key_terms: keyTerms,
        language: 'zh'
    });

    fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: body
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullContent = '';

        function processStream() {
            return reader.read().then(({done, value}) => {
                if (done) {
                    return;
                }

                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.error) {
                                streamOutput.innerHTML = `<p style="color: var(--danger);">生成失败：${data.error}</p>`;
                                return;
                            }
                            if (data.chunk) {
                                fullContent += data.chunk;
                                streamOutput.innerHTML = fullContent + '<span class="cursor"></span>';
                                streamOutput.scrollTop = streamOutput.scrollHeight;
                            }
                            if (data.done) {
                                // 生成完成
                                streamOutput.innerHTML = fullContent;
                                sessionStorage.setItem('contract_content', data.content || fullContent);
                                sessionStorage.setItem('contract_title', data.title || 'AI 生成合同');

                                // 添加预览按钮
                                const actions = document.createElement('div');
                                actions.className = 'form-actions';
                                actions.innerHTML = `
                                    <button class="btn btn-primary" onclick="window.location.href='/preview'">
                                        📄 预览并导出合同
                                    </button>
                                    <button class="btn btn-outline" onclick="copyToClipboard()">
                                        📋 复制内容
                                    </button>
                                `;
                                streamOutput.appendChild(actions);
                                return;
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                }

                return processStream();
            });
        }

        return processStream();
    })
    .catch(err => {
        streamOutput.innerHTML = `<p style="color: var(--danger);">请求失败：${err.message}</p>`;
    });
}

// ============ 复制到剪贴板 ============
function copyToClipboard() {
    const content = sessionStorage.getItem('contract_content');
    if (!content) {
        showNotification('没有可复制的内容', 'error');
        return;
    }

    // 将 HTML 转换为纯文本
    const temp = document.createElement('div');
    temp.innerHTML = content;
    const text = temp.innerText || temp.textContent;

    navigator.clipboard.writeText(text).then(() => {
        showNotification('已复制到剪贴板', 'success');
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showNotification('已复制到剪贴板', 'success');
    });
}

// ============ 页面初始化 ============
document.addEventListener('DOMContentLoaded', function() {
    // 检查 URL 参数
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('mode') === 'ai') {
        // 切换到 AI 模式
        switchMode('ai');

        // 恢复之前填写的内容
        const desc = sessionStorage.getItem('ai_description');
        const type = sessionStorage.getItem('ai_contract_type');
        const partyA = sessionStorage.getItem('ai_party_a');
        const partyB = sessionStorage.getItem('ai_party_b');

        if (desc) {
            const descEl = document.getElementById('aiDescription');
            if (descEl) descEl.value = desc;
        }
        if (type) {
            const typeEl = document.getElementById('aiContractType');
            if (typeEl) typeEl.value = type;
        }
        if (partyA) {
            const el = document.getElementById('aiPartyA');
            if (el) el.value = partyA;
        }
        if (partyB) {
            const el = document.getElementById('aiPartyB');
            if (el) el.value = partyB;
        }

        // 清除 sessionStorage
        sessionStorage.removeItem('ai_description');
        sessionStorage.removeItem('ai_contract_type');
        sessionStorage.removeItem('ai_party_a');
        sessionStorage.removeItem('ai_party_b');
    }
});
