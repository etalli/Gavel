# Gavel

[English](README.md)

<img src="docs/images/icon-128.png" alt="Gavel icon" align="right"/>

[Claude Code](https://claude.ai/code) の物理コントローラー。

**なぜ「Gavel（木槌）」？** 裁判官の木槌は判決を確定させます——そして、ここでは常に人間が判断を下す側です。同じキーはどんなキーボードでも送れますが、専用のデバイスがあることで、無意識にキーを叩く代わりに立ち止まって考えるようになります。反射ではなく、判断として。

---

## 機能

- **入力** — 3 つの物理ボタンで Claude Code のパーミッションプロンプトに回答します（`1` 一回許可 / `2` 常に許可 / `3` 拒否）。キーボードを触る必要はありません。
- **出力** — Claude Code のフックイベントに応じて LED が点灯し、Claude の動作をリアルタイムでフィードバックします。

---

## ハードウェア

2 つのボードに対応：

| ボード | LED 出力 |
|-------|---------|
| Raspberry Pi Pico | 3× 個別 LED (GP2/GP3/GP4) |
| Waveshare RP2040 Zero | 内蔵 RGB NeoPixel (GP16) |

ボードの種類は自動検出されます——手動設定は不要です。

どちらも同じ GPIO ピンをボタンに使用します (GP14/GP15/GP26)。ピンの割り当て詳細は [`hardware/wiring.md`](hardware/wiring.md) を参照してください。

![PCB r0](docs/images/PCB-r0.png)

---

## 仕組み

マイコンは 1 本の USB ケーブルで 2 つの独立した役割を担います：

1. **USB HID キーボード** — ボタンを押すと、対応するキーが端末に送信されます。Claude Code はユーザーが直接タイプしたかのように受信します。Claude Code の特別な設定は不要です。

2. **シリアルリスナー** — Claude Code フックが Mac 側の Python スクリプトを呼び出し、マイコンの USB シリアルポートへ小さな JSON メッセージを送信して LED を制御します。

| フック | LED の反応 |
|------|-----------|
| `PreToolUse` | 全 LED 点灯 |
| `PostToolUse` | 全 LED 消灯 |
| `Notification` (info) | ゆっくり 1 回点滅 |
| `Notification` (warn) | 中程度で 3 回点滅 |
| `Notification` (error) | 速く 5 回点滅（赤のみ） |
| `PostToolUse`（コンテキスト 90% 以上） | 中程度で 3 回点滅、その後消灯 |

---

## セットアップ

1. ボードに [CircuitPython](https://circuitpython.org) をインストール
2. CircuitPython のバージョンに合った [CircuitPython ライブラリバンドル](https://circuitpython.org/libraries) をダウンロード
3. 以下を `CIRCUITPY/lib/` にコピー：
   - `adafruit_hid/`（フォルダ）— 全ボードで必要
   - `neopixel.mpy` — Waveshare RP2040 Zero のみ必要
4. `firmware/boot.py` と `firmware/code.py` を `CIRCUITPY` ドライブにコピー
5. `boot.py` を有効にするため、ボードの**電源を入れ直す**（USB を抜き差し）
6. Mac 側の依存関係をインストール：`pip3 install pyserial`
7. [`hardware/wiring.md`](hardware/wiring.md) に従ってボタンと LED を配線
8. `./install.sh --deploy` を実行して `~/.claude/settings.json` にフックを登録

またはインストールスクリプトをそのまま実行：

```bash
./install.sh
```

`--deploy` オプションでフックを `~/.claude/gavel/` にインストールします。プロジェクトフォルダのパスが変わっても安定して動作します：

```bash
./install.sh --deploy
```

プロジェクトフォルダを移動・リネームする予定がある場合に推奨します。

---

## トラブルシューティング

**フックスクリプトを端末から手動実行しても LED が反応しない**

```
No module named 'serial'
```

お使いの端末セッションの `python3` に `pyserial` がインストールされていない可能性があります。以下で修正してください：

```bash
pip3 install pyserial
```

注意：Claude Code のフックは異なる Python 環境を使用する場合があり、その環境にはすでに `pyserial` がインストールされている可能性があります。そのため、端末での手動テストが失敗しても、Claude Code セッション内ではフックが正常に動作することがあります。

---

## ライセンス

MIT ライセンス — 詳細は [LICENSE](LICENSE) を参照してください。
