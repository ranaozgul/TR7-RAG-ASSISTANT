let currentSessionId = localStorage.getItem("luna_session_id");
if (!currentSessionId) {
    currentSessionId = crypto.randomUUID();
    localStorage.setItem("luna_session_id", currentSessionId);
}

// Sayfa yüklendiğinde oturumları listele ve mevcut sohbeti aç
window.addEventListener("DOMContentLoaded", async () => {
    await loadSessions();
    await loadHistory(currentSessionId);
});

// Sol Paneli Gizle/Göster
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("hidden");
}

// Mesaj HTML yapısını oluşturan yardımcı fonksiyon
function createMessageHTML(text, role, id = "") {
    const cssClass = role === 'user' ? 'user-message' : 'bot-message';
    const idAttr = id ? `id="${id}"` : "";
    return `
        <div class="message ${cssClass}" ${idAttr}>
            <div class="message-content">${text}</div>
            <div class="message-actions">
                <button class="dots-btn">⋮</button>
                <div class="action-menu">
                    <button onclick="copyMsg(this)">Kopyala</button>
                    <button onclick="deleteMsg(this)" class="delete-text">Sil</button>
                </div>
            </div>
        </div>
    `;
}

// Yeni Sohbet Başlat
async function startNewChat() {
    currentSessionId = crypto.randomUUID();
    localStorage.setItem("luna_session_id", currentSessionId);
    
    await fetch('/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: currentSessionId, title: "Yeni Sohbet" })
    });

    const chatBox = document.getElementById("chatBox");
    chatBox.innerHTML = createMessageHTML("Merhaba! Ben TR7 teknik destek asistanıyım. Yaşadığınız sorunu veya hata kodunu iletirseniz size yardımcı olabilirim.", "bot");
    await loadSessions();

    const inputFieldEl = document.getElementById("userInput");
    const sendBtnEl = document.querySelector(".send-btn");
    const inputWrapperEl = document.querySelector(".input-wrapper");
    
    inputFieldEl.disabled = false;
    sendBtnEl.disabled = false;
    inputWrapperEl.classList.remove("input-disabled");
    inputFieldEl.placeholder = "Sorunuzu buraya yazın...";
}

// Oturum Listesini Çek ve Göster
async function loadSessions() {
    try {
        const res = await fetch('/sessions');
        const data = await res.json();
        
        const sessionList = document.getElementById("sessionsList");
        if (sessionList) {
            sessionList.innerHTML = '';
            
            data.sessions.forEach(session => {
                const sessionItem = document.createElement("div");
                
                if (session.session_id === currentSessionId) {
                    sessionItem.className = "session-item active";
                } else {
                    sessionItem.className = "session-item";
                }
                
                sessionItem.onclick = () => switchSession(session.session_id);

                const titleSpan = document.createElement("span");
                titleSpan.innerText = session.title;

                const deleteBtn = document.createElement("button");
                deleteBtn.className = "delete-session";
                deleteBtn.innerHTML = "✖"; 
                deleteBtn.onclick = (event) => {
                    event.stopPropagation();
                    showDeleteModal(session.session_id);
                };

                sessionItem.appendChild(titleSpan);
                sessionItem.appendChild(deleteBtn);
                sessionList.appendChild(sessionItem);
            });
        }
    } catch (e) {
        console.error("Oturumlar yüklenemedi:", e);
    }
}

// Başka bir sohbete geçiş yap
async function switchSession(sessionId) {
    currentSessionId = sessionId;
    localStorage.setItem("luna_session_id", currentSessionId);

    const inputFieldEl = document.getElementById("userInput");
    const sendBtnEl = document.querySelector(".send-btn");
    const inputWrapperEl = document.querySelector(".input-wrapper");
    
    inputFieldEl.disabled = false;
    sendBtnEl.disabled = false;
    inputWrapperEl.classList.remove("input-disabled");
    inputFieldEl.placeholder = "Sorunuzu buraya yazın...";

    await loadHistory(sessionId);
    await loadSessions();
}

// Belirli bir oturumun geçmişini ekrana bas
async function loadHistory(sessionId) {
    try {
        const res = await fetch(`/history/${sessionId}`);
        const data = await res.json();
        const chatBox = document.getElementById("chatBox");
        chatBox.innerHTML = '';

        if (data.history && data.history.length > 0) {
            let sonDurumKilitliMi = false;

            data.history.forEach(h => {
                chatBox.insertAdjacentHTML('beforeend', createMessageHTML(h.user_message, 'user'));
                
                if (h.state === "BLOCKED") {
                    const blockedHTML = `
                        <div class="message blocked-message">
                            <div class="message-content">${h.bot_message}</div>
                            <div class="message-actions">
                                <button class="dots-btn">⋮</button>
                                <div class="action-menu">
                                    <button onclick="copyMsg(this)">Kopyala</button>
                                    <button onclick="deleteMsg(this)" class="delete-text">Sil</button>
                                </div>
                            </div>
                        </div>
                    `;
                    chatBox.insertAdjacentHTML('beforeend', blockedHTML);
                    sonDurumKilitliMi = true; 
                } else {
                    chatBox.insertAdjacentHTML('beforeend', createMessageHTML(h.bot_message, 'bot'));
                    sonDurumKilitliMi = false;
                }
            });

            if (sonDurumKilitliMi) {
                const inputFieldEl = document.getElementById("userInput");
                const sendBtnEl = document.querySelector(".send-btn");
                const inputWrapperEl = document.querySelector(".input-wrapper");
                
                inputFieldEl.disabled = true;
                sendBtnEl.disabled = true;
                inputWrapperEl.classList.add("input-disabled");
                inputFieldEl.placeholder = "Güvenlik ihlali tespit edildi. Sohbet kilitlendi.";
            }

        } else {
            chatBox.innerHTML = createMessageHTML("Merhaba! Ben TR7 teknik destek asistanıyım. Yaşadığınız sorunu veya hata kodunu iletirseniz size yardımcı olabilirim.", "bot");
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (e) {
        console.error("Geçmiş yüklenemedi:", e);
    }
}

// --- ÖZEL MODAL İLE SOHBET SİLME İŞLEMLERİ ---
let itemToDeleteId = null; 

function showDeleteModal(id) {
    itemToDeleteId = id; 
    const modal = document.getElementById('custom-confirm-modal');
    if (modal) {
        modal.classList.remove('hidden'); 
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const cancelBtn = document.getElementById('modal-cancel-btn');
    const confirmBtn = document.getElementById('modal-confirm-btn');
    const modal = document.getElementById('custom-confirm-modal');

    if (cancelBtn) {
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (modal) modal.classList.add('hidden');
            itemToDeleteId = null;
        });
    }

    if (confirmBtn) {
        confirmBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            if (itemToDeleteId !== null) {
                const targetId = itemToDeleteId;
                
                if (modal) modal.classList.add('hidden');
                itemToDeleteId = null;

                try {
                    const res = await fetch(`/sessions/${targetId}`, {
                        method: 'DELETE'
                    });

                    if (res.ok) {
                        if (currentSessionId === targetId) {
                            document.getElementById("chatBox").innerHTML = "";
                            await startNewChat(); 
                        } else {
                            await loadSessions();
                        }
                    } else {
                        console.error("Silme işlemi sunucu tarafından reddedildi.");
                    }

                } catch (error) {
                    console.error("Silme işlemi sırasında hata oluştu:", error);
                }
            }
        });
    }
});

// --- TÜM SOHBETİ KOPYALAMA ÖZELLİĞİ ---
function copyAllChat() {
    const chatBox = document.getElementById("chatBox");
    const messages = chatBox.querySelectorAll('.message');
    
    if (messages.length === 0) {
        alert("Kopyalanacak sohbet bulunmuyor!");
        return;
    }

    let fullChatText = "--- TR7 LUNA SOHBET GEÇMİŞİ ---\n\n";

    messages.forEach(msg => {
        const isUser = msg.classList.contains('user-message');
        const content = msg.querySelector('.message-content') ? msg.querySelector('.message-content').innerText : "";
        
        const sender = isUser ? "Kullanıcı" : "TR7 Asistan";
        fullChatText += `${sender}:\n${content}\n\n-----------------------------------\n\n`;
    });

    navigator.clipboard.writeText(fullChatText).then(() => {
        const btn = document.querySelector('.icon-copy-btn');
        
        // Kopyalandığında simgeyi tik işaretiyle değiştir
        btn.innerHTML = "✅";
        btn.style.backgroundColor = "#CFD6C4"; // Soft yeşil
        
        setTimeout(() => {
            btn.innerHTML = "📋"; // Eski panoya kopyala simgesine dön
            btn.style.backgroundColor = "";
        }, 2000);
    }).catch(err => {
        console.error('Tüm sohbet kopyalanamadı: ', err);
    });
}

// Mesaj Gönderme
async function sendMessage() {
    const inputField = document.getElementById("userInput");
    const chatBox = document.getElementById("chatBox");
    const text = inputField.value.trim();
    if(!text) return;

    const personaSelect = document.getElementById("persona");
    const secilenTavir = personaSelect ? personaSelect.value : "resmi";

    chatBox.insertAdjacentHTML('beforeend', createMessageHTML(text, 'user'));

    inputField.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    const botMsgId = "bot-msg-" + Date.now();
    chatBox.insertAdjacentHTML('beforeend', createMessageHTML("Düşünüyor...", "bot", botMsgId));
    chatBox.scrollTop = chatBox.scrollHeight;

    const botContentDiv = document.getElementById(botMsgId).querySelector('.message-content');

    try {
        const sessionTitle = text.length > 25 ? text.substring(0, 25) + "..." : text;
        await fetch('/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, title: sessionTitle })
        });

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                question: text, 
                session_id: currentSessionId,
                tavir: secilenTavir
            })
        });
        
        const data = await response.json();
        
        if (data.is_blocked) {
            const botMsgElement = document.getElementById(botMsgId);
            botMsgElement.classList.remove('bot-message');
            botMsgElement.classList.add('blocked-message');
            
            const inputFieldEl = document.getElementById("userInput");
            const sendBtnEl = document.querySelector(".send-btn");
            const inputWrapperEl = document.querySelector(".input-wrapper");
            
            inputFieldEl.disabled = true;
            sendBtnEl.disabled = true;
            inputWrapperEl.classList.add("input-disabled");
            inputFieldEl.placeholder = "Güvenlik ihlali tespit edildi. Sohbet kilitlendi.";
        }

        botContentDiv.innerText = data.response || data.answer || JSON.stringify(data);
        await loadSessions();
    } catch (error) {
        console.error("Fetch Hatası:", error); 
        botContentDiv.innerText = "Bağlantı hatası oluştu.";
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

function checkEnter(event) {
    if(event.key === 'Enter') {
        sendMessage();
    }
}

// --- 3 NOKTA MENÜSÜ İŞLEVLERİ ---
function copyMsg(button) {
    const messageContainer = button.closest('.message');
    const textContent = messageContainer.querySelector('.message-content').innerText;
    
    navigator.clipboard.writeText(textContent).then(() => {
        const originalText = button.innerText;
        button.innerText = "Kopyalandı!";
        button.style.color = "#657166"; 
        button.style.fontWeight = "bold";
        
        setTimeout(() => {
            button.innerText = originalText;
            button.style.color = ""; 
            button.style.fontWeight = "";
        }, 2000);
    }).catch(err => {
        console.error('Kopyalama başarısız: ', err);
    });
}

function deleteMsg(button) {
    const messageContainer = button.closest('.message');
    messageContainer.classList.add('deleting');
    
    setTimeout(() => {
        messageContainer.remove();
    }, 300);
}