# ai-market-watchdog-mxn STATUS

最終更新: 2026-05-01
担当者: dev-dept
現在の状態: 🔧 運用

## 概要

MXN/JPY レートを 24 時間監視し、急変動時に AI（GPT-4o-mini）が相場解説を生成するバッチ Bot。
Google Cloud Run Jobs + Cloud Scheduler で毎時自動実行。稼働中。

## 進捗ハイライト（直近）

- 2026-05-01: Phase 1 完了。日本語ファイルを docs/internal/ へ移動、README を FX_Margin_Simulator 基準フォーマットに統一、Mermaid アーキテクチャ図追加。master へ push 済み。
- 2026-01-10: Slack 統合版（ID015）が完成し、本リポはベース版として安定稼働継続
- 2026-01-04: トラブルシューティング記録（GCP 認証・Python バージョン問題等）

## 次のアクション

- [ ] (P1) スクリーンショット撮影・README の `<!-- TODO: screenshot -->` に差し込み（社長手動）
- [ ] (P2) Phase 2: pytest 追加（現時点でテスト未整備）
- [ ] (P2) Phase 2: GitHub Actions CI（pytest 自動実行）
- [ ] (P3) Phase 3: CHANGELOG.md / CONTRIBUTING.md 追加

## 残課題・blocker

- スクリーンショット: 社長手動領域（GCP コンソールの実行ログ画面を想定）
- テスト未整備: main.py が単一ファイル構成のため Phase 2 で pytest 設計から着手要

## 関連ファイル

- 実装: `main.py`（単一ファイル、監視・AI分析ロジック）
- GCP 再作成手順: `recreation_commands.md`
- 社内ドキュメント: `docs/internal/`
- GitHub: https://github.com/tomomira/ai-market-watchdog-mxn
- 関連 note 記事: ID002（https://note.com/lively_hippo6176/n/nff0d7792bf5b）
