import logging

logger = logging.getLogger(__name__)

def register_dynamic_models(sender, **kwargs):
    """
    post_migrateシグナルで動的モデルを登録する。
    """
    from .models import register_dynamic_model

    models_to_register = [
        ("Evaluation", "Evaluation", "evaluation"),
        ("Decision", "Decision", "decision"),
        ("Recognition", "Recognition", "recognition"),
    ]

    for model_name, schema_name, table_name in models_to_register:
        try:
            print(f"[TRACE] Attempting to register dynamic model: {model_name}")
            register_dynamic_model(model_name, schema_name, table_name)
            logger.info(f"[SUCCESS] Dynamic model '{model_name}' registered successfully.")
        except Exception as e:
            logger.error(f"[ERROR] Error registering dynamic model '{model_name}': {e}")
            print(f"[ERROR] Error registering model '{model_name}': {e}")
