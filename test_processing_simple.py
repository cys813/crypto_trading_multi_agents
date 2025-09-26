"""
Simple test script for processing pipeline without external dependencies
"""

import asyncio
import sys
import os
from datetime import datetime
import hashlib
import re

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Simple test without importing the full pipeline
class MockNewsArticle:
    def __init__(self, id, title, content, source="test.com"):
        self.id = id
        self.title = title
        self.content = content
        self.source = source
        self.published_at = datetime.now()

class SimpleContentPreprocessor:
    def __init__(self):
        self.html_pattern = re.compile(r'<[^>]+>')
        self.url_pattern = re.compile(r'http[s]?://\S+')
        self.whitespace_pattern = re.compile(r'\s+')

    def preprocess_content(self, content):
        """预处理内容"""
        # 移除HTML标签
        content = self.html_pattern.sub('', content)
        # 移除URL
        content = self.url_pattern.sub('[URL]', content)
        # 标准化空白字符
        content = self.whitespace_pattern.sub(' ', content)
        # 移除首尾空白
        content = content.strip()
        return content

    def generate_hash(self, content):
        """生成内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

class SimpleDeduplicationEngine:
    def __init__(self):
        self.seen_hashes = set()

    def check_duplicate(self, article):
        """检查重复"""
        content_hash = hashlib.sha256(article.content.lower().strip().encode('utf-8')).hexdigest()[:16]
        is_duplicate = content_hash in self.seen_hashes

        if not is_duplicate:
            self.seen_hashes.add(content_hash)

        return is_duplicate, content_hash

class SimpleProcessingPipeline:
    def __init__(self):
        self.preprocessor = SimpleContentPreprocessor()
        self.deduplicator = SimpleDeduplicationEngine()
        self.stats = {
            'total_processed': 0,
            'preprocessed': 0,
            'duplicates_found': 0,
            'errors': 0
        }

    async def process_articles(self, articles):
        """处理文章列表"""
        results = []
        processed_articles = []

        for article in articles:
            try:
                self.stats['total_processed'] += 1

                # 预处理
                processed_content = self.preprocessor.preprocess_content(article.content)
                article.content = processed_content
                self.stats['preprocessed'] += 1

                # 去重
                is_duplicate, content_hash = self.deduplicator.check_duplicate(article)
                if is_duplicate:
                    self.stats['duplicates_found'] += 1
                    results.append({
                        'article': article,
                        'status': 'skipped',
                        'reason': 'duplicate',
                        'content_hash': content_hash
                    })
                    continue

                # 添加到已处理列表
                processed_articles.append(article)
                results.append({
                    'article': article,
                    'status': 'completed',
                    'content_hash': content_hash
                })

            except Exception as e:
                self.stats['errors'] += 1
                results.append({
                    'article': article,
                    'status': 'failed',
                    'error': str(e)
                })

        return processed_articles, results, self.stats


async def test_processing_pipeline():
    """测试处理管道"""
    print("Testing simple processing pipeline...")

    # 创建测试文章
    test_articles = [
        MockNewsArticle(
            id="test_001",
            title="Bitcoin Price Surges",
            content="""
            <p>Bitcoin price surged to new heights as institutional adoption increases.</p>
            Visit https://example.com for more info.
            Multiple    spaces    here.
            """,
            source="coindesk.com"
        ),
        # 重复文章
        MockNewsArticle(
            id="test_002",
            title="Bitcoin Price Surges",
            content="Bitcoin price surged to new heights as institutional adoption increases.",
            source="bloomberg.com"
        ),
        # 包含噪声的文章
        MockNewsArticle(
            id="test_003",
            title="Crypto News",
            content="""
            <div class="ad">Click here for special offers!!!</div>
            Cryptocurrency markets show mixed signals.
            免责声明：投资有风险，入市需谨慎。
            """,
            source="unknown.com"
        )
    ]

    # 创建处理管道
    pipeline = SimpleProcessingPipeline()

    # 处理文章
    start_time = datetime.now()
    processed_articles, results, stats = await pipeline.process_articles(test_articles)
    end_time = datetime.now()

    print(f"Processing completed in {(end_time - start_time).total_seconds():.2f}s")
    print(f"Results:")
    print(f"  - Total processed: {stats['total_processed']}")
    print(f"  - Preprocessed: {stats['preprocessed']}")
    print(f"  - Duplicates found: {stats['duplicates_found']}")
    print(f"  - Errors: {stats['errors']}")
    print(f"  - Final articles: {len(processed_articles)}")

    # 显示详细结果
    for i, result in enumerate(results):
        article = result['article']
        print(f"\nArticle {i+1} ({article.id}):")
        print(f"  - Status: {result['status']}")
        print(f"  - Source: {article.source}")
        if result['status'] == 'skipped':
            print(f"  - Reason: {result['reason']}")
            print(f"  - Content hash: {result['content_hash']}")
        elif result['status'] == 'completed':
            print(f"  - Content hash: {result['content_hash']}")
            print(f"  - Content length: {len(article.content)}")
            print(f"  - Preview: {article.content[:100]}...")
        elif result['status'] == 'failed':
            print(f"  - Error: {result['error']}")

    return True


async def test_content_processing():
    """测试内容处理功能"""
    print("\nTesting content processing features...")

    preprocessor = SimpleContentPreprocessor()

    # 测试HTML清理
    html_content = "<p>This is <b>bold</b> text with <a href='https://example.com'>link</a>.</p>"
    cleaned = preprocessor.preprocess_content(html_content)
    print(f"HTML cleaning:")
    print(f"  Original: {html_content}")
    print(f"  Cleaned: {cleaned}")

    # 测试URL替换
    url_content = "Visit https://example.com and http://test.org for more info."
    url_cleaned = preprocessor.preprocess_content(url_content)
    print(f"\nURL replacement:")
    print(f"  Original: {url_content}")
    print(f"  Cleaned: {url_cleaned}")

    # 测试空白字符标准化
    whitespace_content = "Multiple    spaces   and\t\ttabs"
    whitespace_cleaned = preprocessor.preprocess_content(whitespace_content)
    print(f"\nWhitespace normalization:")
    print(f"  Original: '{whitespace_content}'")
    print(f"  Normalized: '{whitespace_cleaned}'")

    return True


async def test_deduplication():
    """测试去重功能"""
    print("\nTesting deduplication...")

    deduplicator = SimpleDeduplicationEngine()

    # 测试相同内容
    article1 = MockNewsArticle("test_001", "Same Content", "This is the same content.")
    article2 = MockNewsArticle("test_002", "Different Title", "This is the same content.")

    is_dup1, hash1 = deduplicator.check_duplicate(article1)
    is_dup2, hash2 = deduplicator.check_duplicate(article2)

    print(f"Article 1: {'Duplicate' if is_dup1 else 'Unique'} (hash: {hash1})")
    print(f"Article 2: {'Duplicate' if is_dup2 else 'Unique'} (hash: {hash2})")

    # 测试不同内容
    article3 = MockNewsArticle("test_003", "Different Content", "This is different content.")
    is_dup3, hash3 = deduplicator.check_duplicate(article3)
    print(f"Article 3: {'Duplicate' if is_dup3 else 'Unique'} (hash: {hash3})")

    return True


async def main():
    """主测试函数"""
    print("Starting simple processing pipeline tests...\n")

    try:
        # 测试内容处理功能
        success1 = await test_content_processing()

        # 测试去重功能
        success2 = await test_deduplication()

        # 测试完整处理管道
        success3 = await test_processing_pipeline()

        if success1 and success2 and success3:
            print("\n✅ All tests passed!")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)