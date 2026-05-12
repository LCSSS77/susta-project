import sys
import os
import json
from datetime import datetime
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, 
                             QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QFrame, QLabel, QMessageBox,
                             QListWidget, QDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# --- PAGE D'ACCUEIL ---
PAGE_ACCUEIL_SUSTA = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;900&display=swap" rel="stylesheet">
    <style>
        body { 
            background: radial-gradient(circle at center, #0B1026 0%, #000000 100%) !important;
            height: 100vh; overflow: hidden; display: flex; font-family: 'Orbitron', sans-serif;
            justify-content: center; align-items: center; flex-direction: column; margin: 0;
            cursor: crosshair; color: #0ff;
        }
        .logo-home { font-size: 120px; font-weight: 900; text-shadow: 0 0 20px #0ff; margin-bottom: 20px; }
        .points-display { font-size: 24px; color: #ff00ff; margin-bottom: 30px; text-shadow: 0 0 10px #f0f; }
        input {
            width: 550px; padding: 22px 35px; border-radius: 45px; border: 2px solid #0ff;
            background: rgba(255,255,255,0.05); color: white; font-size: 20px; outline: none;
            box-shadow: 0 0 25px rgba(0,255,255,0.3); text-align: center;
        }
        .particle { position: absolute; background: #0ff; border-radius: 50%; pointer-events: none; animation: fadeOut 0.8s linear forwards; }
        @keyframes fadeOut { 0% { transform: scale(1); opacity: 1; } 100% { transform: scale(0); opacity: 0; } }
    </style>
</head>
<body>
    <div class="logo-home">susta</div>
    <div class="points-display">CRÉDITS : <span id="points">0</span> PTS</div>
    <input type="text" placeholder="EXPLORER L'UNIVERS..." onkeydown="if(event.key === 'Enter') window.location.href = 'https://www.google.com/search?q=' + this.value">
    <script>
        document.addEventListener('mousemove', function(e) {
            let p = document.createElement('div'); p.className = 'particle';
            let s = Math.random() * 8 + 2; p.style.width = s+'px'; p.style.height = s+'px';
            p.style.left = e.pageX+'px'; p.style.top = e.pageY+'px';
            document.body.appendChild(p); setTimeout(() => p.remove(), 800);
        });
    </script>
</body>
</html>
"""

class HistoryDialog(QDialog):
    def __init__(self, history_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("susta - logs")
        self.setFixedSize(500, 600)
        self.setStyleSheet("background-color: #050505; border: 1px solid #0ff;")
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("QListWidget { background: #000; color: #ff00ff; border: none; font-family: monospace; }")
        for item in reversed(history_list): self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

class SustaBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("susta")
        self.resize(1350, 950)
        self.points = 0
        self.history = []
        self.charger_donnees()

        self.browser = QWebEngineView()
        self.browser.setHtml(PAGE_ACCUEIL_SUSTA)

        # --- BARRE DE NAVIGATION ---
        nav_container = QFrame()
        nav_container.setFixedHeight(70)
        nav_container.setStyleSheet("background-color: #000; border-bottom: 2px solid #0ff;")
        nav_layout = QHBoxLayout(nav_container)
        
        self.mini_logo = QLabel("susta")
        self.mini_logo.setStyleSheet("color: #0ff; font-family: 'Orbitron'; font-weight: 900; font-size: 28px; margin-right: 10px;")
        
        btn_style = "QPushButton { background: #111; color: #0ff; border: 1px solid #0ff; border-radius: 18px; width: 36px; height: 36px; font-weight: bold; } QPushButton:hover { background: #0ff; color: #000; }"
        
        self.btn_back = QPushButton("‹")
        self.btn_back.setStyleSheet(btn_style)
        self.btn_back.clicked.connect(self.browser.back)

        self.btn_reload = QPushButton("⟳")
        self.btn_reload.setStyleSheet(btn_style)
        self.btn_reload.clicked.connect(self.browser.reload)

        self.btn_logs = QPushButton("LOGS")
        self.btn_logs.setFixedWidth(70)
        self.btn_logs.setStyleSheet("QPushButton { background: #111; color: #f0f; border: 1px solid #f0f; border-radius: 10px; font-size: 10px; font-weight: bold; }")
        self.btn_logs.clicked.connect(self.show_history)

        self.btn_collect = QPushButton("⚡ RÉCOLTER")
        self.btn_collect.setFixedWidth(120)
        self.update_collect_button_style()
        self.btn_collect.clicked.connect(self.clic_recompense)

        self.url_bar = QLineEdit()
        self.url_bar.setStyleSheet("QLineEdit { background: #111; color: #0ff; border: 1px solid #333; border-radius: 18px; padding: 0 20px; height: 36px; }")
        self.url_bar.returnPressed.connect(self.naviguer)

        nav_layout.addWidget(self.mini_logo)
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_reload)
        nav_layout.addWidget(self.btn_logs)
        nav_layout.addWidget(self.btn_collect)
        nav_layout.addWidget(self.url_bar)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(nav_container)
        layout.addWidget(self.browser)
        self.setCentralWidget(container)
        
        # NETTOYEUR AGRESSIF (toutes les 2 secondes)
        self.timer = QTimer()
        self.timer.timeout.connect(self.overdrive_style)
        self.timer.start(2000)

        self.browser.urlChanged.connect(self.maj_barre)
        self.browser.loadFinished.connect(self.enregistrer_historique)

    def charger_donnees(self):
        self.path = os.path.expanduser("~/.susta_data.json")
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                data = json.load(f)
                self.points = data.get("points", 0)
                self.last_login = data.get("last_login", "")
                self.history = data.get("history", [])
        else: self.points, self.last_login, self.history = 0, "", []

    def sauvegarder_donnees(self):
        with open(self.path, "w") as f:
            json.dump({"points": self.points, "last_login": self.last_login, "history": self.history}, f)

    def overdrive_style(self):
        # On ne lance le script que si on n'est pas sur la home
        url = self.browser.url().toString()
        if url != "" and url != "about:blank":
            script = """
            (function() {
                // 1. Forcer le VIOLET et le NOIR
                if(!document.getElementById('susta-style')){
                    var s = document.createElement('style'); s.id = 'susta-style';
                    s.innerHTML = 'html, body { background: #050505 !important; color: #0ff !important; } a, h1, h2, h3, em, .LC20lb { color: #f0f !important; text-decoration: none !important; } #logo, .logo, img[alt*="Google"], svg.gb_tc { display:none !important; }';
                    document.head.appendChild(s);
                }
                // 2. Remplacer Google par Susta en haut à gauche
                if(!document.getElementById('susta-injected')){
                    var t = document.createElement('div'); t.id = 'susta-injected';
                    t.innerHTML = 'susta'; t.style.cssText = 'position:fixed; top:15px; left:20px; color:#0ff; font-family:Orbitron, sans-serif; font-size:22px; font-weight:90 + 0; z-index:999999; text-shadow: 0 0 10px #0ff;';
                    document.body.appendChild(t);
                }
            })();
            """
            self.browser.page().runJavaScript(script)
            # Mise à jour des points sur la home
            self.browser.page().runJavaScript(f"if(document.getElementById('points')) document.getElementById('points').innerText = '{self.points}';")

    def show_history(self):
        dialog = HistoryDialog(self.history, self)
        dialog.exec()

    def update_collect_button_style(self):
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        if self.last_login == aujourdhui:
            self.btn_collect.setEnabled(False)
            self.btn_collect.setStyleSheet("QPushButton { background: #222; color: #555; border: 1px solid #333; border-radius: 10px; }")
        else:
            self.btn_collect.setStyleSheet("QPushButton { background: #000; color: #0ff; border: 2px solid #0ff; border-radius: 10px; font-weight: bold; }")

    def clic_recompense(self):
        self.points += 100
        self.last_login = datetime.now().strftime("%Y-%m-%d")
        self.sauvegarder_donnees()
        self.update_collect_button_style()
        QMessageBox.information(self, "SUSTA", "100 Points récoltés !")

    def enregistrer_historique(self):
        url = self.browser.url().toString()
        if url != "about:blank" and url != "" and (not self.history or self.history[-1] != url):
            self.history.append(url)
            if len(self.history) > 100: self.history.pop(0)
            self.sauvegarder_donnees()

    def naviguer(self):
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')): url = 'https://www.google.com/search?q=' + url
        self.browser.setUrl(QUrl(url))

    def maj_barre(self, q):
        self.url_bar.setText(q.toString() if q.toString() != "about:blank" else "")

app = QApplication(sys.argv)
fenetre = SustaBrowser()
fenetre.show()
sys.exit(app.exec())