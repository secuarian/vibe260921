"""네이버 뉴스 크롤러 GUI (PyQt6).

크롤링 로직은 news_crawler.py를 재사용한다.
실행: python news_crawler_gui.py
필요 패키지: PyQt6, requests, beautifulsoup4
"""
import html
import json
import sys
import time

import requests
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton, QSpinBox,
    QSplitter, QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout,
    QWidget, QAbstractItemView,
)

from news_crawler import (
    DELAY, SEARCH_URL, fetch, parse_article, parse_search_results, save_excel,
)


class CrawlWorker(QThread):
    """네트워크 요청을 별도 스레드에서 실행해 화면이 멈추지 않게 한다."""
    found = pyqtSignal(int)        # 발견한 기사 수
    article = pyqtSignal(int, dict)  # (행 번호, 기사 정보)
    progress = pyqtSignal(int)     # 완료한 기사 수
    failed = pyqtSignal(str)
    finished_ok = pyqtSignal()

    def __init__(self, query, limit, fetch_body):
        super().__init__()
        self.query = query
        self.limit = limit
        self.fetch_body = fetch_body
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            if self.query:
                soup = fetch("https://search.naver.com/search.naver",
                             {"where": "news", "query": self.query})
            else:
                soup = fetch(SEARCH_URL)
            items = parse_search_results(soup, self.limit)
            self.found.emit(len(items))

            for i, art in enumerate(items):
                if self._stop:
                    break
                if self.fetch_body and art["naver_url"]:
                    try:
                        art.update(parse_article(art["naver_url"]))
                    except requests.RequestException as e:
                        art["content"] = f"(본문 수집 실패: {e})"
                    time.sleep(DELAY)
                self.article.emit(i, art)
                self.progress.emit(i + 1)
            self.finished_ok.emit()
        except requests.RequestException as e:
            self.failed.emit(f"요청 실패: {e}")
        except Exception as e:  # 예상치 못한 파싱 오류도 화면에 표시
            self.failed.emit(f"오류: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("네이버 뉴스 크롤러")
        self.resize(1100, 680)
        self.articles = []
        self.worker = None

        # ----- 상단 입력줄 -----
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText("검색어 (비워두면 기본 URL: 반도체)")
        self.query_edit.returnPressed.connect(self.start)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 30)
        self.count_spin.setValue(10)
        self.count_spin.setSuffix(" 건")
        self.body_check = QCheckBox("본문 수집")
        self.body_check.setChecked(True)
        self.search_btn = QPushButton("크롤링 시작")
        self.search_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton("중지")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        self.save_btn = QPushButton("JSON 저장")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_json)
        self.excel_btn = QPushButton("엑셀 저장")
        self.excel_btn.setEnabled(False)
        self.excel_btn.clicked.connect(self.save_excel_file)

        top = QHBoxLayout()
        top.addWidget(QLabel("검색어"))
        top.addWidget(self.query_edit, 1)
        top.addWidget(self.count_spin)
        top.addWidget(self.body_check)
        top.addWidget(self.search_btn)
        top.addWidget(self.stop_btn)
        top.addWidget(self.save_btn)
        top.addWidget(self.excel_btn)

        # ----- 결과 표 + 상세 -----
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["제목", "언론사", "시간"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.itemSelectionChanged.connect(self.show_detail)

        self.detail = QTextBrowser()
        self.detail.setOpenExternalLinks(True)
        self.detail.setPlaceholderText("기사를 선택하면 내용이 여기에 표시됩니다.")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.table)
        splitter.addWidget(self.detail)
        splitter.setSizes([520, 580])

        # ----- 하단 상태 -----
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().showMessage("준비됨")

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.addLayout(top)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(root)

    # ---------- 동작 ----------
    def start(self):
        if self.worker and self.worker.isRunning():
            return
        self.articles = []
        self.table.setRowCount(0)
        self.detail.clear()
        self.save_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # 목록 조회 중에는 무한 진행 표시
        self.statusBar().showMessage("검색 결과를 가져오는 중...")

        self.worker = CrawlWorker(
            self.query_edit.text().strip(),
            self.count_spin.value(),
            self.body_check.isChecked(),
        )
        self.worker.found.connect(self.on_found)
        self.worker.article.connect(self.on_article)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished_ok.connect(self.on_done)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def stop(self):
        if self.worker:
            self.worker.stop()
            self.statusBar().showMessage("중지하는 중...")

    def on_found(self, count):
        self.articles = [None] * count
        self.table.setRowCount(count)
        self.progress.setRange(0, max(count, 1))
        self.progress.setValue(0)
        self.statusBar().showMessage(f"기사 {count}건 발견, 수집 중...")

    def on_article(self, row, art):
        self.articles[row] = art
        for col, key in enumerate(("title", "press", "time")):
            self.table.setItem(row, col, QTableWidgetItem(art[key]))
        if row == 0:
            self.table.selectRow(0)

    def on_done(self):
        n = sum(a is not None for a in self.articles)
        self.statusBar().showMessage(f"완료: {n}건 수집")

    def on_failed(self, msg):
        self.statusBar().showMessage("실패")
        QMessageBox.warning(self, "크롤링 실패", msg)

    def on_finished(self):
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)
        has_data = any(self.articles)
        self.save_btn.setEnabled(has_data)
        self.excel_btn.setEnabled(has_data)

    def show_detail(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        art = self.articles[rows[0].row()] if rows[0].row() < len(self.articles) else None
        if not art:
            return
        esc = html.escape
        body = art.get("content") or art.get("snippet") or "(내용 없음)"
        links = f'<a href="{esc(art["url"])}">원문 보기</a>'
        if art["naver_url"]:
            links += f' &nbsp;|&nbsp; <a href="{esc(art["naver_url"])}">네이버 뉴스</a>'
        self.detail.setHtml(
            f'<h3>{esc(art["title"])}</h3>'
            f'<p style="color:gray">{esc(art["press"])} · '
            f'{esc(art.get("date") or art["time"])}</p>'
            f'<p>{links}</p><hr>'
            f'<p style="line-height:150%">{esc(body).replace(chr(10), "<br>")}</p>'
        )

    def save_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "JSON으로 저장", "news.json", "JSON (*.json)")
        if not path:
            return
        data = [a for a in self.articles if a]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "저장 실패", str(e))
            return
        self.statusBar().showMessage(f"{len(data)}건을 {path}에 저장했습니다.")

    def save_excel_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "엑셀로 저장", "news.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        data = [a for a in self.articles if a]
        try:
            save_excel(data, path)
        except PermissionError:
            QMessageBox.warning(
                self, "저장 실패",
                "파일에 쓸 수 없습니다. 같은 이름의 엑셀 파일이 열려 있다면 닫고 다시 시도하세요.")
            return
        except Exception as e:
            QMessageBox.warning(self, "저장 실패", str(e))
            return
        self.statusBar().showMessage(f"{len(data)}건을 {path}에 저장했습니다.")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
