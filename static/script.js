// Nav Bar Hamburger Menu
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }

    // Nav linklerine tıklandığında menüyü kapat
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
        });
    });
});

// BMI Calculator Helper
function calculateBMI() {
    const weight = prompt("Kilonuzu kg olarak giriniz:");
    const height = prompt("Boyunuzu metre olarak giriniz (örn: 1.70):");
    
    if (weight && height && !isNaN(weight) && !isNaN(height) && parseFloat(height) > 0) {
        const bmi = (parseFloat(weight) / (parseFloat(height) * parseFloat(height))).toFixed(1);
        document.getElementById('bmi').value = bmi;
        
        let category = '';
        if (bmi < 18.5) category = 'Zayıf';
        else if (bmi < 25) category = 'Normal';
        else if (bmi < 30) category = 'Fazla Kilolu';
        else category = 'Obez';
        
        alert(`BMI değeriniz: ${bmi} (${category})`);
    } else {
        alert("Lütfen geçerli kilo ve boy değerleri giriniz.");
    }
}

// Risk Form Handler
document.addEventListener('DOMContentLoaded', function() {
    const riskForm = document.getElementById('riskForm');
    if (riskForm) {
        riskForm.addEventListener('submit', handleRiskTest);
    }
});

async function handleRiskTest(event) {
    event.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoading = submitBtn.querySelector('.btn-loading');
    const resultDiv = document.getElementById('result');

    // Loading state
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline-block';
    resultDiv.innerHTML = ''; // Önceki sonucu temizle

    try {
        const formData = new FormData(event.target);

        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Sunucu hatası. Lütfen daha sonra tekrar deneyin.');
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        displayResult(data);

    } catch (error) {
        console.error('Hata:', error);
        resultDiv.innerHTML = `
            <div class="result" style="background: #ffe6e6; color: #e53e3e; border: 1px solid #e53e3e; padding: 1.5rem; border-radius: 12px; margin-top: 2rem;">
                <p>Bir hata oluştu: ${error.message}. Lütfen tüm alanları doğru girdiğinizden emin olun.</p>
            </div>
        `;
    } finally {
        // Reset state
        submitBtn.disabled = false;
        submitBtn.classList.remove('loading');
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

function displayResult(data) {
    const resultDiv = document.getElementById('result');
    const riskClass = data.risk_class;
    
    let progressColor = 'var(--low-risk-color)';
    if (riskClass === 'medium-risk') progressColor = 'var(--medium-risk-color)';
    else if (riskClass === 'high-risk') progressColor = 'var(--high-risk-color)';

    const actionsHtml = data.actions.map(action => `<li><i class="fas fa-check-circle"></i> ${action}</li>`).join('');

    resultDiv.innerHTML = `
        <div class="result-card ${riskClass}">
            <div class="result-header">
                <h3>Risk Testi Sonucu</h3>
                <div class="result-score">
                    <p class="score-text">Tahmini Risk</p>
                    <span class="score-value">${data.risk_percentage}%</span>
                </div>
            </div>
            <div class="result-content">
                <h4>Risk Seviyesi: <span class="risk-level">${data.risk_level}</span></h4>
                <p class="recommendation">${data.recommendation}</p>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${data.risk_percentage}%; background-color: ${progressColor};"></div>
                </div>
                <h5>Önerilen Aksiyonlar:</h5>
                <ul class="actions-list">
                    ${actionsHtml}
                </ul>
            </div>
        </div>
    `;
}

// Chatbot İşlevleri
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    if (chatInput && sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
});

async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const message = chatInput.value.trim();

    if (!message) return;

    // Kullanıcının mesajını göster
    const userMessageDiv = document.createElement('div');
    userMessageDiv.classList.add('message', 'user-message');
    userMessageDiv.innerHTML = `<p>${message}</p>`;
    chatMessages.appendChild(userMessageDiv);
    
    chatInput.value = '';
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Bot mesajı için "yazıyor..." göstergesi
    const botTypingDiv = document.createElement('div');
    botTypingDiv.classList.add('message', 'bot-message', 'typing-indicator');
    botTypingDiv.innerHTML = `<p>...</p>`;
    chatMessages.appendChild(botTypingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const response = await fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // "yazıyor..." göstergesini kaldır ve bot mesajını ekle
            chatMessages.removeChild(botTypingDiv);
            const botMessageDiv = document.createElement('div');
            botMessageDiv.classList.add('message', 'bot-message');
            botMessageDiv.innerHTML = `<p>${data.response}</p>`;
            chatMessages.appendChild(botMessageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            chatMessages.removeChild(botTypingDiv);
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('message', 'bot-message');
            errorDiv.innerHTML = `<p>Üzgünüm, bir hata oluştu: ${data.error}</p>`;
            chatMessages.appendChild(errorDiv);
        }
    } catch (error) {
        chatMessages.removeChild(botTypingDiv);
        const errorDiv = document.createElement('div');
        errorDiv.classList.add('message', 'bot-message');
        errorDiv.innerHTML = `<p>Ağ hatası: Lütfen internet bağlantınızı kontrol edin.</p>`;
        chatMessages.appendChild(errorDiv);
    }
}

// MHRS bağlantısı
function openMHRS() {
    window.open('https://www.mhrs.gov.tr/', '_blank');
}