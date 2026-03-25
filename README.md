# Photo OCR Viewer (Windows向け最小構成)

PySide6 + PaddleOCR で作った、ローカル完結のシンプルなフォトOCRビューアです。  
単一フォルダ内の画像（png/jpg/jpeg）を前後移動しながら、OCR結果の枠表示・テキスト選択・コピーができます。

## 機能

- 画像表示
- フォルダ内の Previous / Next 移動
- 画像表示時の自動OCR
- OCR検出枠のオーバーレイ表示
- 枠クリックでOCR行を選択
- 右パネルのOCR行クリックで対応枠をハイライト
- 選択行コピー
- 全文コピー
- 実行中メモリキャッシュ（同じ画像の再OCRを回避）

## 構成

- `src/photo_ocr_viewer/main.py` : UI本体
- `src/photo_ocr_viewer/ocr.py` : PaddleOCRラッパー + キャッシュ
- `requirements.txt` : 依存ライブラリ
- `photo_ocr_viewer.spec` : PyInstallerビルド用spec

## 前提

- Python 3.10 以上推奨
- Windows 11 想定
- 初回OCR時はモデルダウンロードで時間がかかる場合があります

## ローカル実行手順

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
python -m photo_ocr_viewer.main
```

> PowerShell の場合:
>
> ```powershell
> .\.venv\Scripts\Activate.ps1
> $env:PYTHONPATH = "src"
> python -m photo_ocr_viewer.main
> ```

## 使い方

1. アプリ起動
2. **Open Folder** で画像フォルダを選択
3. 画像が表示され、自動でOCR実行
4. **Previous / Next** で移動
5. 画像上のOCR枠をクリック、または右側行リストをクリックして選択
6. **Copy** または **Copy Selected** で選択行コピー
7. **Copy Full Text** で全文コピー
8. **Re-run OCR** で現在画像のOCRを再実行

## PyInstallerでWindows EXEビルド

```bash
.venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --clean --noconfirm photo_ocr_viewer.spec
```

出力先:

- `dist/photo-ocr-viewer/photo-ocr-viewer.exe`

## 注意点

- OCR精度は画像品質に依存します
- 日本語向けに `lang="japan"` を使用しています
- 完全オフライン運用には、初回モデル取得後にモデルキャッシュを含めた配布設計が必要です
