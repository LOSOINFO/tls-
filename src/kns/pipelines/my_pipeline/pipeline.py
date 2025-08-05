from kedro.pipeline import Pipeline, node, pipeline

def dummy_node():
    print("✅ Kedro pipeline executed!")

def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(dummy_node, inputs=None, outputs=None, name="dummy_node")
    ])
