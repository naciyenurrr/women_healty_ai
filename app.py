from flask import Flask, request, jsonify, render_template_string, send_from_directory
import numpy as np
import joblib
import os
import logging
import traceback
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random

# Flask uygulaması
app = Flask(__name__, static_folder='static')

# CORS desteği
try:
    from flask_cors import CORS
    CORS(app)
    app.logger.info("✅ CORS desteği etkinleştirildi")
except ImportError:
    app.logger.info("ℹ️ CORS modülü bulunamadı")

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global değişkenler
model = None
faq_data = []

# ==============================
# MODELLERİ YÜKLEME FONKSİYONLARI
# ==============================

def load_model():
    """ML modelini yükle"""
    global model
    try:
        model_path = os.path.join(os.path.dirname(__file__), "cancer.pkl")
        if os.path.exists(model_path):
            model = joblib.load(model_path)
            logger.info("✅ Makine öğrenmesi modeli başarıyla yüklendi.")
            return True
        else:
            logger.warning(f"⚠️ Model dosyası bulunamadı: {model_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Model yüklenirken hata: {str(e)}")
        return False

def load_faq_data():
    """FAQ verilerini JSON dosyasından yükle"""
    global faq_data
    try:
        faq_path = os.path.join(os.path.dirname(__file__), "faq.json")
        if os.path.exists(faq_path):
            with open(faq_path, "r", encoding="utf-8") as f:
                faq_data = json.load(f)
            logger.info(f"✅ FAQ verileri yüklendi: {len(faq_data)} kayıt")
            return True
        else:
            logger.error(f"❌ faq.json dosyası bulunamadı: {faq_path}")
            return False
    except Exception as e:
        logger.error(f"❌ FAQ yüklenirken hata: {str(e)}")
        return False

# ==============================
# CHATBOT SINIFI
# ==============================

class CustomHealthChatbot:
    """Kadın sağlığı chatbot'u - TF-IDF ve Cosine Similarity ile geliştirilmiş versiyon"""

    def __init__(self):
        self.vectorizer = None
        self.faq_vectors = None
        self.faq_data = []

        # Karşılama mesajları
        self.greeting_keywords = [
            'merhaba', 'selam', 'hello', 'hi', 'iyi günler', 'günaydın',
            'iyi akşamlar', 'selamlar', 'selamun aleyküm'
        ]
        self.greeting_responses = [
            "Merhaba! Kadın sağlığı konusunda size nasıl yardımcı olabilirim?",
            "Selam! Sağlık sorularınızı yanıtlamak için buradayım.",
            "İyi günler! Kadın sağlığıyla ilgili sorularınızı sorabilirsiniz."
        ]

        # Teşekkür yanıtları
        self.thanks_keywords = [
            'teşekkür', 'teşekkürler', 'sağol', 'sağolun', 'thanks',
            'thank you', 'merci', 'eyvallah'
        ]
        self.thanks_responses = [
            "Rica ederim, her zaman buradayım!",
            "Bir şey değil, sağlığınız her şeyden önemli.",
            "Memnun oldum yardımcı olabildiysem!"
        ]

    def train_tfidf(self, faq_data):
        """FAQ verilerini TF-IDF ile vektörleştir"""
        if not faq_data:
            logger.error("❌ TF-IDF eğitimi için yeterli veri yok!")
            return False

        questions = [item['question'] for item in faq_data]
        self.vectorizer = TfidfVectorizer()
        self.faq_vectors = self.vectorizer.fit_transform(questions)
        self.faq_data = faq_data
        logger.info(f"✅ TF-IDF eğitimi tamamlandı. {len(faq_data)} soru işlendi.")
        return True

    def find_best_answer(self, user_message):
        """Kullanıcının sorusuna en uygun cevabı bul"""
        if self.faq_vectors is None or self.vectorizer is None:
            return None, 0.0

        # Kullanıcı mesajını vektörleştir
        user_vec = self.vectorizer.transform([user_message])

        # Benzerlikleri hesapla
        similarities = cosine_similarity(user_vec, self.faq_vectors)

        # En yüksek benzerlik skorunu bul
        best_idx = similarities.argmax()
        best_score = similarities[0, best_idx]

        return self.faq_data[best_idx], best_score

    def friendly_response(self, answer):
        """Samimi bir yanıt üret"""
        starters = [
            "Anladım, bu konuda şöyle bir bilgi verebilirim: ",
            "Tabii ki, bu önemli bir konu. Bilmeniz gerekenler şunlar: ",
            "Bu konuda sıkça sorulan bilgilerden biri: "
        ]
        endings = [
            "\n\nEğer durum devam ederse mutlaka bir doktora danışın.",
            "\n\nUnutmayın, her bireyin durumu farklıdır. Profesyonel destek alın.",
            "\n\nSağlık konularında emin olmadığınız durumlarda mutlaka bir uzmana başvurun."
        ]
        return random.choice(starters) + answer + random.choice(endings)

    def generate_response(self, message):
        """Kullanıcı mesajına yanıt üret"""
        message = message.strip().lower()

        # Selamlama kontrolü
        if any(keyword in message for keyword in self.greeting_keywords):
            return random.choice(self.greeting_responses)

        # Teşekkür kontrolü
        if any(keyword in message for keyword in self.thanks_keywords):
            return random.choice(self.thanks_responses)

        # En iyi cevabı bul
        best_match, score = self.find_best_answer(message)

        # Eşik değeri kontrolü
        if best_match and score > 0.25:
            return self.friendly_response(best_match['answer'])
        else:
            return (
                "Üzgünüm, sorunuz için kesin bir bilgi bulamadım.\n\n"
                "Size yardımcı olabileceğim bazı konular:\n"
                "• Adet düzensizlikleri\n"
                "• Gebelik ve doğum\n"
                "• Menopoz\n"
                "• Kadın hastalıkları\n"
                "• HPV ve smear testleri\n\n"
                "Daha spesifik bir soru sorabilir misiniz?"
            )

# ==============================
# UYGULAMA BAŞLATMA
# ==============================

chatbot = CustomHealthChatbot()

def initialize_app():
    """Uygulamayı başlat ve verileri yükle"""
    logger.info("🚀 Kadın Sağlığı Chatbot başlatılıyor...")
    load_model()
    if load_faq_data():
        chatbot.train_tfidf(faq_data)

with app.app_context():
    initialize_app()

# ==============================
# ROUTES - WEB SAYFALARI
# ==============================

@app.route('/')
def index():
    """Ana sayfa"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "index.html dosyası bulunamadı!", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    """Static dosyaları servis et"""
    try:
        return send_from_directory('.', filename)
    except:
        return "Dosya bulunamadı", 404

# ==============================
# API ENDPOINTS
# ==============================

@app.route("/predict", methods=["POST"])
def predict():
    """Risk analizi endpoint'i"""
    try:
        if model is None:
            return jsonify({
                "error": "Model yüklenemedi. Lütfen daha sonra tekrar deneyin.",
                "status": "error"
            }), 500

        # Form verilerini al
        age = float(request.form.get('age', 0))
        height = float(request.form.get('height', 0))
        weight = float(request.form.get('weight', 0))
        smoking = int(request.form.get('smoking', 0))
        genetic_risk = int(request.form.get('genetic_risk', 0))
        physical_activity = int(request.form.get('physical_activity', 0))
        alcohol_intake = int(request.form.get('alcohol_intake', 0))
        cancer_history = int(request.form.get('cancer_history', 0))

        # BMI hesapla
        height_m = height / 100
        bmi = weight / (height_m * height_m)

        # Veri doğrulama
        if age < 18 or age > 120:
            raise ValueError("Yaş 18-120 arasında olmalıdır")
        if bmi < 10 or bmi > 60:
            raise ValueError("BMI değeri makul aralıkta değil")

        # Modeli kullan
        features = np.array([[age, bmi, smoking, genetic_risk, physical_activity, 
                            alcohol_intake, cancer_history]])
        
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0]

        # Risk yüzdesini hesapla
        risk_percentage = int(probability[1] * 100) if len(probability) > 1 else int(prediction * 100)

        # Risk seviyesini belirle
        if risk_percentage < 30:
            risk_level = "Düşük Risk"
            risk_class = "low-risk"
            recommendation = "Mevcut sağlık durumunuz iyi görünüyor. Düzenli kontroller ve sağlıklı yaşam tarzını sürdürün."
            actions = [
                "Yılda bir kez rutin sağlık kontrolü yaptırın",
                "Sağlıklı beslenme alışkanlıklarını sürdürün",
                "Düzenli egzersiz yapın",
                "Stres yönetimi tekniklerini uygulayın"
            ]
        elif risk_percentage < 60:
            risk_level = "Orta Risk"
            risk_class = "medium-risk"
            recommendation = "Dikkat edilmesi gereken faktörler bulunuyor. Doktor kontrolü ve yaşam tarzı değişiklikleri önerilir."
            actions = [
                "6 ayda bir doktor kontrolü yaptırın",
                "Beslenme uzmanına danışın",
                "Egzersiz programınızı artırın",
                "Zararlı alışkanlıklardan kaçının",
                "Tarama testlerini aksatmayın"
            ]
        else:
            risk_level = "Yüksek Risk"
            risk_class = "high-risk"
            recommendation = "Acil doktor konsültasyonu ve detaylı inceleme gerekiyor. Hemen bir uzmana başvurun."
            actions = [
                "En kısa sürede bir uzmana başvurun",
                "Kapsamlı sağlık taraması yaptırın",
                "Genetik danışmanlık alın",
                "Yaşam tarzınızı radikal şekilde değiştirin",
                "Düzenli takip programına başlayın"
            ]

        return jsonify({
            "risk_percentage": risk_percentage,
            "risk_level": risk_level,
            "risk_class": risk_class,
            "recommendation": recommendation,
            "actions": actions,
            "status": "success"
        })

    except ValueError as ve:
        return jsonify({
            "error": f"Geçersiz veri: {str(ve)}",
            "status": "error"
        }), 400
    except Exception as e:
        logger.error(f"Prediction hata: {str(e)}")
        return jsonify({
            "error": "Analiz sırasında bir hata oluştu. Lütfen form bilgilerinizi kontrol edin.",
            "status": "error"
        }), 500

@app.route("/chatbot", methods=["POST"])
def chat():
    """Chatbot endpoint'i"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type application/json olmalıdır"}), 400

        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Mesaj bulunamadı"}), 400

        message = data["message"].strip()
        if not message:
            return jsonify({"error": "Boş mesaj gönderilemez"}), 400

        if len(message) > 500:
            return jsonify({"error": "Mesaj çok uzun. (max 500 karakter)"}), 400

        response = chatbot.generate_response(message)
        logger.info(f"Chatbot - Soru: {message[:50]}... | Yanıt uzunluğu: {len(response)}")

        return jsonify({
            "response": response,
            "status": "success",
            "faq_count": len(faq_data),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Chatbot hatası: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": "Chatbot geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin.",
            "status": "error"
        }), 500

# ==============================
# HATA YÖNETİCİLERİ
# ==============================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Sayfa bulunamadı"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Sunucu hatası"}), 500

# ==============================
# ANA UYGULAMA
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("🚀 Sağlık Chatbot API Başlatılıyor...")
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)