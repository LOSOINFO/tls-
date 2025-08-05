from typing import Dict
from kedro.pipeline import Pipeline
from kns.pipelines.my_pipeline.pipeline import create_pipeline  # ✅ manual import

def register_pipelines() -> Dict[str, Pipeline]:
    return {
        "__default__": create_pipeline()
    }
