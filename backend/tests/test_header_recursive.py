import pytest

class TestHeaderOrder:
    def test_merge_preserves_header_order(self):
        """测试 headers 合并后应保持原始顺序（保序去重）"""
        prev_headers = ["# 第一章", "## 1.1 介绍", "### 1.1.1 背景"]
        curr_headers = ["# 第一章", "## 1.1 介绍", "### 1.1.2 细节"]
        merged = list(dict.fromkeys(prev_headers + curr_headers))
        # 验证层级顺序：顶级标题必须在最前
        assert merged[0] == "# 第一章", f"顶级标题应排第一：{merged}"
        assert merged[1] == "## 1.1 介绍", f"二级标题应排第二：{merged}"
        assert "### 1.1.1 背景" in merged
        assert "### 1.1.2 细节" in merged
        idx_111 = merged.index("### 1.1.1 背景")
        idx_112 = merged.index("### 1.1.2 细节")
        assert idx_111 < idx_112, f"顺序错误：{merged}"

    def test_set_breaks_header_order(self):
        """验证 set() 会破坏 header 顺序（反向测试）"""
        prev_headers = ["# 第一章", "## 1.1 介绍", "### 1.1.1 背景"]
        curr_headers = ["# 第一章", "## 1.1 介绍", "### 1.1.2 细节"]
        merged_set = list(set(prev_headers + curr_headers))
        # set 不保证顺序，顶级标题不一定在最前
        # 此测试验证 set() 方法不可靠
        assert merged_set[0] != "# 第一章" or merged_set[1] != "## 1.1 介绍", \
            f"set() 碰巧顺序正确（小概率）：{merged_set}"

    def test_stitch_preserves_header_order(self):
        """测试 stitch_chunks_with_headers 合并后 headers 保持顺序"""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Text_segmentation'))
        from header_recursive import stitch_chunks_with_headers

        prev = {
            "page_start": 1, "page_end": 1, "pages": [1],
            "text": "# 第一章\n## 1.1 介绍\n### 1.1.1 背景\n一些内容",
            "text_length": 30, "continued": False,
            "cross_page_bridge": False, "is_table_like": False,
            "headers": ["# 第一章", "## 1.1 介绍", "### 1.1.1 背景"]
        }
        curr = {
            "page_start": 1, "page_end": 1, "pages": [1],
            "text": "更多延续内容",
            "text_length": 7, "continued": False,
            "cross_page_bridge": False, "is_table_like": False,
            "headers": ["# 第一章", "## 1.1 介绍", "### 1.1.2 细节"]
        }

        stitched = stitch_chunks_with_headers([prev, curr], chunk_size=600, respect_headers=False)

        assert len(stitched) == 1, f"应该合并为1个chunk，实际{len(stitched)}"
        merged_headers = stitched[0]["headers"]
        # 关键断言：顶级标题必须在最前
        assert merged_headers[0] == "# 第一章", f"顶级标题应排第一：{merged_headers}"
        assert merged_headers[1] == "## 1.1 介绍", f"二级标题应排第二：{merged_headers}"
        idx_111 = merged_headers.index("### 1.1.1 背景")
        idx_112 = merged_headers.index("### 1.1.2 细节")
        assert idx_111 < idx_112, f"子标题顺序错误：{merged_headers}"
