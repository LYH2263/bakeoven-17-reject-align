import os

# 必须在导入 app.* 之前：app.database 在导入时按 DATABASE_URL 创建引擎
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SEED_ON_EMPTY", "false")
