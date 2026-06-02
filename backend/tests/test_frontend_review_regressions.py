from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_repo_file(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dashboard_upload_refresh_callback_uses_react_ref():
    dashboard = read_repo_file("frontend/components/Dashboard.tsx")

    assert "useRef" in dashboard
    assert "const fetchStatsRef = useRef<" in dashboard
    assert "const fetchStatsRef = { current:" not in dashboard


def test_upload_polling_result_gates_success_toast():
    upload_dialog = read_repo_file("frontend/components/UploadDialog.tsx")

    assert "): Promise<ProcessingResult>" in upload_dialog
    assert "success: false" in upload_dialog
    assert "处理超时，文件可能已上传成功，请刷新页面确认" in upload_dialog
    assert "if (!processingResult.success)" in upload_dialog
    assert "toast.error(`${file.name} 处理状态未确认`" in upload_dialog
    assert "Async path — poll completed" not in upload_dialog


def test_public_demo_files_do_not_expose_private_evidence_context():
    public_files = [
        "docs/retro/2026-06-01-weekly.md",
        "frontend/components/Dashboard.tsx",
        "frontend/styles/globals.css",
    ]
    forbidden = [
        "evidence" + "_pack",
        "~/" + "Developer/" + "Car" + "eer",
        "/" + "Users/" + "mac/" + "Developer/" + "Car" + "eer",
        "Car" + "eer" + " directory",
        "API key" + " in Git history",
        "B" + "FG",
        "filter" + "-branch",
        "面" + "试",
        "interview" + "-demo",
    ]

    for repo_path in public_files:
        contents = read_repo_file(repo_path)
        for term in forbidden:
            assert term not in contents, f"{term!r} leaked in {repo_path}"


def test_dashboard_retrieval_quick_action_navigates_to_retrieval_view():
    dashboard = read_repo_file("frontend/components/Dashboard.tsx")

    assert "action.id === 3 && onNavigate" in dashboard
    assert "onNavigate('retrieval')" in dashboard


def test_professional_app_v2_does_not_apply_legacy_theme_text_overrides():
    css = read_repo_file("frontend/styles/globals.css")

    assert ".theme-v2:not(.professional-app) .text-sm" in css
    assert ".theme-v2 .text-sm,\n.theme-v2 small" not in css
    assert ".theme-v2:not(.professional-app) button" in css
    assert ".theme-v2 button {\n  color: #1a1a1a;" not in css
