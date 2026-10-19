"""
BÁJALO - descargador MP4 / MP3 con estética cassette / VHS.

Requisitos:
    pip install PySide6 yt-dlp
    FFmpeg instalado y en el PATH

Uso:
    python bajalo.py
"""
import os
import re
import shutil
import sys
from pathlib import Path

import yt_dlp
from PySide6.QtCore import QRectF, QThread, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QFileDialog, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

# Paleta (4 colores)
CREMA, CARBON, ROJO, MOSTAZA = "#F1E6CC", "#1C1B19", "#E8432E", "#F0B429"
FUENTES = ["Space Mono", "Consolas", "Courier New", "monospace"]

def recurso(nombre):
    """Ruta a un archivo junto al programa (también funciona dentro de un .exe de PyInstaller)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return str(base / nombre)


def carpeta_bin():
    """Carpeta con ffmpeg/ffprobe/deno incluidos en el programa (si existe)."""
    b = Path(recurso("bin"))
    return b if (b / "ffmpeg.exe").exists() else None


QSS = """
QWidget { background: @CREMA; color: @CARBON; }
QLineEdit { border: 3px solid @CARBON; padding: 10px; font-size: 14px; }
QPushButton { border: 3px solid @CARBON; padding: 10px 14px; font-weight: bold; }
QPushButton:hover { background: @MOSTAZA; }
QPushButton:checked { background: @CARBON; color: @CREMA; }
QPushButton#go { background: @ROJO; color: @CREMA; font-size: 18px; padding: 14px; }
QPushButton#go:hover { background: @CARBON; }
QPushButton#go:disabled { background: @MOSTAZA; color: @CARBON; }
QLabel#titulo { font-size: 40px; font-weight: bold; }
QLabel#sub { font-size: 11px; }
QLabel#osd { font-size: 13px; font-weight: bold; }
"""
for k, v in {"@CREMA": CREMA, "@CARBON": CARBON, "@ROJO": ROJO, "@MOSTAZA": MOSTAZA}.items():
    QSS = QSS.replace(k, v)


class Descarga(QThread):
    progreso = Signal(float)
    estado = Signal(str)
    listo = Signal()
    error = Signal(str)

    def __init__(self, url, formato, carpeta):
        super().__init__()
        self.url, self.formato, self.carpeta = url, formato, carpeta
        self.fase = 0
        self.fases = 2 if formato == "MP4" else 1

    def run(self):
        opts = {
            "outtmpl": str(Path(self.carpeta) / "%(title).150s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
            "progress_hooks": [self._hook],
        }
        if self.formato == "MP3":
            opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{"key": "FFmpegExtractAudio",
                                    "preferredcodec": "mp3",
                                    "preferredquality": "320"}],
            })
        else:
            opts.update({"format": "bestvideo+bestaudio/best",
                         "merge_output_format": "mp4"})
        local = carpeta_bin()
        if local:
            opts["ffmpeg_location"] = str(local)
            if (local / "deno.exe").exists():  # necesario para YouTube
                opts["js_runtimes"] = {"deno": {"path": str(local / "deno.exe")}}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            self.progreso.emit(1.0)
            self.listo.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _hook(self, d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            if total:
                frac = d["downloaded_bytes"] / total
                self.progreso.emit(min((self.fase + frac) / self.fases, 0.99))
        elif d["status"] == "finished":
            self.fase += 1
            self.estado.emit("PROCESANDO")


class Cassette(QWidget):
    """Cassette dibujado a mano: los carretes giran y la cinta pasa de uno a otro."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(190)
        self.angulo, self.progreso = 0.0, 0.0
        self.activo, self.formato = False, "MP4"
        t = QTimer(self)
        t.timeout.connect(self._tick)
        t.start(33)

    def _tick(self):
        if self.activo:
            self.angulo = (self.angulo + 7) % 360
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cw = min(w - 16, (h - 16) * 1.6)
        ch = cw / 1.6
        x, y = (w - cw) / 2, (h - ch) / 2

        # cuerpo
        p.setPen(QPen(QColor(CARBON), 4))
        p.setBrush(QColor(CREMA))
        p.drawRoundedRect(QRectF(x, y, cw, ch), 14, 14)

        # etiqueta
        lab = QRectF(x + cw * 0.07, y + ch * 0.08, cw * 0.86, ch * 0.42)
        p.setPen(QPen(QColor(CARBON), 3))
        p.setBrush(QColor(MOSTAZA))
        p.drawRoundedRect(lab, 6, 6)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(ROJO))
        p.drawRect(QRectF(lab.left() + 2, lab.top() + lab.height() * 0.62, lab.width() - 4, lab.height() * 0.14))
        p.drawRect(QRectF(lab.left() + 2, lab.top() + lab.height() * 0.82, lab.width() - 4, lab.height() * 0.07))

        f = QFont()
        f.setFamilies(FUENTES)
        f.setBold(True)
        f.setPixelSize(max(10, int(ch * 0.14)))
        p.setFont(f)
        p.setPen(QColor(CARBON))
        area = lab.adjusted(10, 4, -10, 0)
        p.drawText(area, Qt.AlignLeft | Qt.AlignTop, "BÁJALO")
        f.setPixelSize(max(8, int(ch * 0.08)))
        p.setFont(f)
        p.drawText(area, Qt.AlignRight | Qt.AlignTop, f"A · {self.formato}")

        # ventana de cinta
        win = QRectF(x + cw * 0.18, y + ch * 0.56, cw * 0.64, ch * 0.30)
        p.setPen(QPen(QColor(CARBON), 3))
        p.setBrush(QColor(CARBON))
        p.drawRoundedRect(win, win.height() / 2, win.height() / 2)

        rmax = win.height() * 0.46
        rmin = rmax * 0.6
        hub = rmax * 0.5
        izq = rmax - (rmax - rmin) * self.progreso
        der = rmin + (rmax - rmin) * self.progreso
        cy = win.center().y()
        for cx, r in ((win.left() + win.height() / 2, izq), (win.right() - win.height() / 2, der)):
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(MOSTAZA))
            p.drawEllipse(QRectF(cx - r, cy - r, 2 * r, 2 * r))
            p.setBrush(QColor(CREMA))
            p.drawEllipse(QRectF(cx - hub, cy - hub, 2 * hub, 2 * hub))
            p.save()
            p.translate(cx, cy)
            p.rotate(self.angulo)
            p.setPen(QPen(QColor(CARBON), 2))
            for _ in range(6):
                p.drawLine(0, 0, int(hub * 0.9), 0)
                p.rotate(60)
            p.restore()

        # tornillos
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(CARBON))
        for sx, sy in ((0.04, 0.06), (0.96, 0.06), (0.04, 0.94), (0.96, 0.94)):
            p.drawEllipse(QRectF(x + cw * sx - 3, y + ch * sy - 3, 6, 6))


class Bajalo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bájalo")
        self.setWindowIcon(QIcon(recurso("bajalo.png")))
        self.resize(520, 600)
        self.setStyleSheet(QSS)
        self.carpeta = str(Path.home() / "Downloads")
        self.hilo = None

        titulo = QLabel("BÁJALO")
        titulo.setObjectName("titulo")
        sub = QLabel("PEGA EL ENLACE  ·  ELIGE  ·  BÁJALO")
        sub.setObjectName("sub")

        self.cassette = Cassette()
        self.url = QLineEdit()
        self.url.setPlaceholderText("PEGA EL ENLACE AQUÍ")

        self.btn_mp4 = QPushButton("MP4 · VIDEO")
        self.btn_mp3 = QPushButton("MP3 · AUDIO")
        grupo = QButtonGroup(self)
        for b in (self.btn_mp4, self.btn_mp3):
            b.setCheckable(True)
            grupo.addButton(b)
            b.clicked.connect(self.cambiar_formato)
        self.btn_mp4.setChecked(True)
        fila_fmt = QHBoxLayout()
        fila_fmt.addWidget(self.btn_mp4)
        fila_fmt.addWidget(self.btn_mp3)

        self.lbl_carpeta = QLabel()
        self._pintar_carpeta()
        btn_carpeta = QPushButton("CARPETA")
        btn_carpeta.clicked.connect(self.elegir_carpeta)
        fila_dir = QHBoxLayout()
        fila_dir.addWidget(self.lbl_carpeta, 1)
        fila_dir.addWidget(btn_carpeta)

        self.go = QPushButton("▶  BÁJALO")
        self.go.setObjectName("go")
        self.go.clicked.connect(self.iniciar)

        self.osd = QLabel("■ STOP")
        self.osd.setObjectName("osd")
        self.osd.setWordWrap(True)

        logo = QLabel()
        logo.setPixmap(QPixmap(recurso("bajalo.png")).scaled(
            64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        textos = QVBoxLayout()
        textos.setSpacing(0)
        textos.addWidget(titulo)
        textos.addWidget(sub)
        cabecera = QHBoxLayout()
        cabecera.setSpacing(14)
        cabecera.addWidget(logo)
        cabecera.addLayout(textos, 1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(12)
        lay.addLayout(cabecera)
        for w in (self.cassette, self.url):
            lay.addWidget(w)
        lay.addLayout(fila_fmt)
        lay.addLayout(fila_dir)
        lay.addWidget(self.go)
        lay.addWidget(self.osd)

        # detecta enlaces copiados al portapapeles
        QGuiApplication.clipboard().dataChanged.connect(self.portapapeles)

    # ---- interfaz ----
    def _pintar_carpeta(self):
        txt = self.carpeta if len(self.carpeta) < 34 else "…" + self.carpeta[-33:]
        self.lbl_carpeta.setText(txt)

    def formato(self):
        return "MP3" if self.btn_mp3.isChecked() else "MP4"

    def cambiar_formato(self):
        self.cassette.formato = self.formato()
        self.cassette.update()

    def elegir_carpeta(self):
        d = QFileDialog.getExistingDirectory(self, "Guardar en", self.carpeta)
        if d:
            self.carpeta = d
            self._pintar_carpeta()

    def portapapeles(self):
        if self.hilo and self.hilo.isRunning():
            return
        txt = QGuiApplication.clipboard().text().strip()
        if re.match(r"https?://\S+$", txt):
            self.url.setText(txt)
            self.osd.setText("◉ ENLACE DETECTADO")

    # ---- descarga ----
    def iniciar(self):
        # si el enlace quedó pegado dos veces, usa solo el primero
        enlaces = re.findall(r"https?://.+?(?=https?://|\s|$)", self.url.text())
        if not enlaces:
            self.osd.setText("✖ PEGA PRIMERO UN ENLACE")
            return
        url = enlaces[0]
        self.url.setText(url)
        if not carpeta_bin() and not shutil.which("ffmpeg"):
            self.osd.setText("✖ FALTA FFMPEG: instálalo y agrégalo al PATH")
            return
        self.go.setEnabled(False)
        self.cassette.progreso = 0.0
        self.cassette.activo = True
        self.osd.setText("● REC 00%")
        self.hilo = Descarga(url, self.formato(), self.carpeta)
        self.hilo.progreso.connect(self.on_progreso)
        self.hilo.estado.connect(self.osd.setText)
        self.hilo.listo.connect(self.on_listo)
        self.hilo.error.connect(self.on_error)
        self.hilo.start()

    def on_progreso(self, v):
        self.cassette.progreso = v
        self.osd.setText(f"● REC {int(v * 100):02d}%")

    def on_listo(self):
        self.cassette.progreso = 1.0
        self._terminar("✔ LISTO · guardado en tu carpeta")

    def on_error(self, msg):
        self._terminar("✖ ERROR · " + msg.replace("ERROR: ", "")[:140])

    def _terminar(self, texto):
        self.cassette.activo = False
        self.cassette.update()
        self.go.setEnabled(True)
        self.osd.setText(texto)


if __name__ == "__main__":
    if sys.platform == "win32":  # ícono propio en la barra de tareas
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bajalo.app")
    for nombre in ("stdout", "stderr"):  # en modo ventana no existen y yt-dlp escribe ahí
        if getattr(sys, nombre) is None:
            setattr(sys, nombre, open(os.devnull, "w"))
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(recurso("bajalo.png")))
    fuente = QFont()
    fuente.setFamilies(FUENTES)
    fuente.setPointSize(10)
    app.setFont(fuente)
    ventana = Bajalo()
    ventana.show()
    sys.exit(app.exec())
