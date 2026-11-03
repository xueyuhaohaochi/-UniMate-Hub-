"""轻量 RAG 知识库：字符级 n-gram + TF-IDF 余弦检索，中文友好、零外部依赖。"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+\-.#]*")


@dataclass
class KBHit:
    file: str
    title: str
    text: str
    score: float = 0.0


def _tokenize(text: str) -> List[str]:
    """中文按单字 + 二字组，英文按词，混合分词无需词典。"""
    text = text.lower()
    zh_only = re.sub(r"[^\u4e00-\u9fff]", " ", text)
    chars = [c for c in zh_only if c != " "]
    bigrams = [chars[i] + chars[i + 1] for i in range(len(chars) - 1)]
    words = _WORD_RE.findall(text)
    return words + bigrams + chars


def _tf(tokens: List[str]) -> dict:
    tf: dict = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    return tf


class KnowledgeBase:
    """加载 knowledge/ 目录下全部 .txt，按空行分块并建立 TF-IDF 索引。"""

    def __init__(self, knowledge_dir: str | Path):
        self.chunks: List[tuple] = []  # (file, title, text, tf)
        self.df: dict = {}
        self.idf: dict = {}
        self.n_docs = 1
        self._load(Path(knowledge_dir))
        self._build_index()

    def _load(self, folder: Path) -> None:
        if not folder.exists():
            return
        for fp in sorted(folder.glob("*.txt")):
            raw = fp.read_text(encoding="utf-8")
            for block in re.split(r"\n\s*\n", raw):
                block = block.strip()
                if not block:
                    continue
                m = re.match(r"【(.+?)】", block)
                title = m.group(1).strip() if m else block.splitlines()[0][:20]
                tf = _tf(_tokenize(block))
                self.chunks.append((fp.name, title, block, tf))
                for t in set(tf):
                    self.df[t] = self.df.get(t, 0) + 1

    def _build_index(self) -> None:
        self.n_docs = max(len(self.chunks), 1)
        self.idf = {t: math.log((self.n_docs + 1) / (c + 1)) + 1.0 for t, c in self.df.items()}

    @staticmethod
    def _weighted(tf: dict, idf: dict) -> dict:
        return {t: (1.0 + math.log(v)) * idf.get(t, 1.0) for t, v in tf.items()}

    def search(self, query: str, k: int = 3, scope: Optional[List[str]] = None) -> List[KBHit]:
        q = self._weighted(_tf(_tokenize(query)), self.idf)
        if not q:
            return []
        q_norm = math.sqrt(sum(v * v for v in q.values())) or 1.0
        hits: List[KBHit] = []
        for file, title, text, tf in self.chunks:
            if scope and file not in scope:
                continue
            d = self._weighted(tf, self.idf)
            d_norm = math.sqrt(sum(v * v for v in d.values())) or 1.0
            small, big = (q, d) if len(q) <= len(d) else (d, q)
            dot = sum(w * big.get(t, 0.0) for t, w in small.items())
            score = dot / (q_norm * d_norm)
            if score > 0.01:
                hits.append(KBHit(file, title, text, round(score, 4)))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]
